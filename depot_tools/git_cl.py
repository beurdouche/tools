#!/usr/bin/env python
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Copyright (C) 2008 Evan Martin <martine@danga.com>

"""A git-command for integrating reviews on Rietveld."""

import json
import logging
import optparse
import os
import re
import stat
import sys
import textwrap
import urlparse
import urllib2

try:
  import readline  # pylint: disable=F0401,W0611
except ImportError:
  pass


from third_party import upload
import breakpad  # pylint: disable=W0611
import fix_encoding
import gclient_utils
import presubmit_support
import rietveld
import scm
import subprocess2
import watchlists


DEFAULT_SERVER = 'https://codereview.appspot.com'
POSTUPSTREAM_HOOK_PATTERN = '.git/hooks/post-cl-%s'
DESCRIPTION_BACKUP_FILE = '~/.git_cl_description_backup'
GIT_INSTRUCTIONS_URL = 'http://code.google.com/p/chromium/wiki/UsingNewGit'


# Initialized in main()
settings = None


def DieWithError(message):
  print >> sys.stderr, message
  sys.exit(1)


def RunCommand(args, error_ok=False, error_message=None, **kwargs):
  try:
    return subprocess2.check_output(args, shell=False, **kwargs)
  except subprocess2.CalledProcessError, e:
    if not error_ok:
      DieWithError(
          'Command "%s" failed.\n%s' % (
            ' '.join(args), error_message or e.stdout or ''))
    return e.stdout


def RunGit(args, **kwargs):
  """Returns stdout."""
  return RunCommand(['git'] + args, **kwargs)


def RunGitWithCode(args):
  """Returns return code and stdout."""
  try:
    out, code = subprocess2.communicate(['git'] + args, stdout=subprocess2.PIPE)
    return code, out[0]
  except ValueError:
    # When the subprocess fails, it returns None.  That triggers a ValueError
    # when trying to unpack the return value into (out, code).
    return 1, ''


def usage(more):
  def hook(fn):
    fn.usage_more = more
    return fn
  return hook


def ask_for_data(prompt):
  try:
    return raw_input(prompt)
  except KeyboardInterrupt:
    # Hide the exception.
    sys.exit(1)


def MatchSvnGlob(url, base_url, glob_spec, allow_wildcards):
  """Return the corresponding git ref if |base_url| together with |glob_spec|
  matches the full |url|.

  If |allow_wildcards| is true, |glob_spec| can contain wildcards (see below).
  """
  fetch_suburl, as_ref = glob_spec.split(':')
  if allow_wildcards:
    glob_match = re.match('(.+/)?(\*|{[^/]*})(/.+)?', fetch_suburl)
    if glob_match:
      # Parse specs like "branches/*/src:refs/remotes/svn/*" or
      # "branches/{472,597,648}/src:refs/remotes/svn/*".
      branch_re = re.escape(base_url)
      if glob_match.group(1):
        branch_re += '/' + re.escape(glob_match.group(1))
      wildcard = glob_match.group(2)
      if wildcard == '*':
        branch_re += '([^/]*)'
      else:
        # Escape and replace surrounding braces with parentheses and commas
        # with pipe symbols.
        wildcard = re.escape(wildcard)
        wildcard = re.sub('^\\\\{', '(', wildcard)
        wildcard = re.sub('\\\\,', '|', wildcard)
        wildcard = re.sub('\\\\}$', ')', wildcard)
        branch_re += wildcard
      if glob_match.group(3):
        branch_re += re.escape(glob_match.group(3))
      match = re.match(branch_re, url)
      if match:
        return re.sub('\*$', match.group(1), as_ref)

  # Parse specs like "trunk/src:refs/remotes/origin/trunk".
  if fetch_suburl:
    full_url = base_url + '/' + fetch_suburl
  else:
    full_url = base_url
  if full_url == url:
    return as_ref
  return None


def print_stats(args):
  """Prints statistics about the change to the user."""
  # --no-ext-diff is broken in some versions of Git, so try to work around
  # this by overriding the environment (but there is still a problem if the
  # git config key "diff.external" is used).
  env = os.environ.copy()
  if 'GIT_EXTERNAL_DIFF' in env:
    del env['GIT_EXTERNAL_DIFF']
  return subprocess2.call(
      ['git', 'diff', '--no-ext-diff', '--stat', '--find-copies-harder'] + args,
      env=env)


class Settings(object):
  def __init__(self):
    self.default_server = None
    self.cc = None
    self.root = None
    self.is_git_svn = None
    self.svn_branch = None
    self.tree_status_url = None
    self.viewvc_url = None
    self.updated = False
    self.is_gerrit = None

  def LazyUpdateIfNeeded(self):
    """Updates the settings from a codereview.settings file, if available."""
    if not self.updated:
      cr_settings_file = FindCodereviewSettingsFile()
      if cr_settings_file:
        LoadCodereviewSettingsFromFile(cr_settings_file)
        self.updated = True
        DownloadHooks(False)
      self.updated = True

  def GetDefaultServerUrl(self, error_ok=False):
    if not self.default_server:
      self.LazyUpdateIfNeeded()
      self.default_server = gclient_utils.UpgradeToHttps(
          self._GetConfig('rietveld.server', error_ok=True))
      if error_ok:
        return self.default_server
      if not self.default_server:
        error_message = ('Could not find settings file. You must configure '
                         'your review setup by running "git cl config".')
        self.default_server = gclient_utils.UpgradeToHttps(
            self._GetConfig('rietveld.server', error_message=error_message))
    return self.default_server

  def GetRoot(self):
    if not self.root:
      self.root = os.path.abspath(RunGit(['rev-parse', '--show-cdup']).strip())
    return self.root

  def GetIsGitSvn(self):
    """Return true if this repo looks like it's using git-svn."""
    if self.is_git_svn is None:
      # If you have any "svn-remote.*" config keys, we think you're using svn.
      self.is_git_svn = RunGitWithCode(
          ['config', '--get-regexp', r'^svn-remote\.'])[0] == 0
    return self.is_git_svn

  def GetSVNBranch(self):
    if self.svn_branch is None:
      if not self.GetIsGitSvn():
        DieWithError('Repo doesn\'t appear to be a git-svn repo.')

      # Try to figure out which remote branch we're based on.
      # Strategy:
      # 1) iterate through our branch history and find the svn URL.
      # 2) find the svn-remote that fetches from the URL.

      # regexp matching the git-svn line that contains the URL.
      git_svn_re = re.compile(r'^\s*git-svn-id: (\S+)@', re.MULTILINE)

      # We don't want to go through all of history, so read a line from the
      # pipe at a time.
      # The -100 is an arbitrary limit so we don't search forever.
      cmd = ['git', 'log', '-100', '--pretty=medium']
      proc = subprocess2.Popen(cmd, stdout=subprocess2.PIPE)
      url = None
      for line in proc.stdout:
        match = git_svn_re.match(line)
        if match:
          url = match.group(1)
          proc.stdout.close()  # Cut pipe.
          break

      if url:
        svn_remote_re = re.compile(r'^svn-remote\.([^.]+)\.url (.*)$')
        remotes = RunGit(['config', '--get-regexp',
                          r'^svn-remote\..*\.url']).splitlines()
        for remote in remotes:
          match = svn_remote_re.match(remote)
          if match:
            remote = match.group(1)
            base_url = match.group(2)
            fetch_spec = RunGit(
                ['config', 'svn-remote.%s.fetch' % remote],
                error_ok=True).strip()
            if fetch_spec:
              self.svn_branch = MatchSvnGlob(url, base_url, fetch_spec, False)
              if self.svn_branch:
                break
            branch_spec = RunGit(
                ['config', 'svn-remote.%s.branches' % remote],
                error_ok=True).strip()
            if branch_spec:
              self.svn_branch = MatchSvnGlob(url, base_url, branch_spec, True)
              if self.svn_branch:
                break
            tag_spec = RunGit(
                ['config', 'svn-remote.%s.tags' % remote],
                error_ok=True).strip()
            if tag_spec:
              self.svn_branch = MatchSvnGlob(url, base_url, tag_spec, True)
              if self.svn_branch:
                break

      if not self.svn_branch:
        DieWithError('Can\'t guess svn branch -- try specifying it on the '
            'command line')

    return self.svn_branch

  def GetTreeStatusUrl(self, error_ok=False):
    if not self.tree_status_url:
      error_message = ('You must configure your tree status URL by running '
                       '"git cl config".')
      self.tree_status_url = self._GetConfig('rietveld.tree-status-url',
                                             error_ok=error_ok,
                                             error_message=error_message)
    return self.tree_status_url

  def GetViewVCUrl(self):
    if not self.viewvc_url:
      self.viewvc_url = gclient_utils.UpgradeToHttps(
          self._GetConfig('rietveld.viewvc-url', error_ok=True))
    return self.viewvc_url

  def GetDefaultCCList(self):
    return self._GetConfig('rietveld.cc', error_ok=True)

  def GetIsGerrit(self):
    """Return true if this repo is assosiated with gerrit code review system."""
    if self.is_gerrit is None:
      self.is_gerrit = self._GetConfig('gerrit.host', error_ok=True)
    return self.is_gerrit

  def _GetConfig(self, param, **kwargs):
    self.LazyUpdateIfNeeded()
    return RunGit(['config', param], **kwargs).strip()


def ShortBranchName(branch):
  """Convert a name like 'refs/heads/foo' to just 'foo'."""
  return branch.replace('refs/heads/', '')


class Changelist(object):
  def __init__(self, branchref=None):
    # Poke settings so we get the "configure your server" message if necessary.
    global settings
    if not settings:
      # Happens when git_cl.py is used as a utility library.
      settings = Settings()
    settings.GetDefaultServerUrl()
    self.branchref = branchref
    if self.branchref:
      self.branch = ShortBranchName(self.branchref)
    else:
      self.branch = None
    self.rietveld_server = None
    self.upstream_branch = None
    self.has_issue = False
    self.issue = None
    self.has_description = False
    self.description = None
    self.has_patchset = False
    self.patchset = None
    self._rpc_server = None
    self.cc = None
    self.watchers = ()
    self._remote = None

  def GetCCList(self):
    """Return the users cc'd on this CL.

    Return is a string suitable for passing to gcl with the --cc flag.
    """
    if self.cc is None:
      base_cc = settings  .GetDefaultCCList()
      more_cc = ','.join(self.watchers)
      self.cc = ','.join(filter(None, (base_cc, more_cc))) or ''
    return self.cc

  def SetWatchers(self, watchers):
    """Set the list of email addresses that should be cc'd based on the changed
       files in this CL.
    """
    self.watchers = watchers

  def GetBranch(self):
    """Returns the short branch name, e.g. 'master'."""
    if not self.branch:
      self.branchref = RunGit(['symbolic-ref', 'HEAD']).strip()
      self.branch = ShortBranchName(self.branchref)
    return self.branch

  def GetBranchRef(self):
    """Returns the full branch name, e.g. 'refs/heads/master'."""
    self.GetBranch()  # Poke the lazy loader.
    return self.branchref

  def FetchUpstreamTuple(self):
    """Returns a tuple containg remote and remote ref,
       e.g. 'origin', 'refs/heads/master'
    """
    remote = '.'
    branch = self.GetBranch()
    upstream_branch = RunGit(['config', 'branch.%s.merge' % branch],
                             error_ok=True).strip()
    if upstream_branch:
      remote = RunGit(['config', 'branch.%s.remote' % branch]).strip()
    else:
      upstream_branch = RunGit(['config', 'rietveld.upstream-branch'],
                               error_ok=True).strip()
      if upstream_branch:
        remote = RunGit(['config', 'rietveld.upstream-remote']).strip()
      else:
        # Fall back on trying a git-svn upstream branch.
        if settings.GetIsGitSvn():
          upstream_branch = settings.GetSVNBranch()
        else:
          # Else, try to guess the origin remote.
          remote_branches = RunGit(['branch', '-r']).split()
          if 'origin/master' in remote_branches:
            # Fall back on origin/master if it exits.
            remote = 'origin'
            upstream_branch = 'refs/heads/master'
          elif 'origin/trunk' in remote_branches:
            # Fall back on origin/trunk if it exists. Generally a shared
            # git-svn clone
            remote = 'origin'
            upstream_branch = 'refs/heads/trunk'
          else:
            DieWithError("""Unable to determine default branch to diff against.
Either pass complete "git diff"-style arguments, like
  git cl upload origin/master
or verify this branch is set up to track another (via the --track argument to
"git checkout -b ...").""")

    return remote, upstream_branch

  def GetUpstreamBranch(self):
    if self.upstream_branch is None:
      remote, upstream_branch = self.FetchUpstreamTuple()
      if remote is not '.':
        upstream_branch = upstream_branch.replace('heads', 'remotes/' + remote)
      self.upstream_branch = upstream_branch
    return self.upstream_branch

  def GetRemote(self):
    if not self._remote:
      self._remote = self.FetchUpstreamTuple()[0]
      if self._remote == '.':

        remotes = RunGit(['remote'], error_ok=True).split()
        if len(remotes) == 1:
          self._remote, = remotes
        elif 'origin' in remotes:
          self._remote = 'origin'
          logging.warning('Could not determine which remote this change is '
                          'associated with, so defaulting to "%s".  This may '
                          'not be what you want.  You may prevent this message '
                          'by running "git svn info" as documented here:  %s',
                          self._remote,
                          GIT_INSTRUCTIONS_URL)
        else:
          logging.warn('Could not determine which remote this change is '
                       'associated with.  You may prevent this message by '
                       'running "git svn info" as documented here:  %s',
                       GIT_INSTRUCTIONS_URL)
    return self._remote

  def GetGitBaseUrlFromConfig(self):
    """Return the configured base URL from branch.<branchname>.baseurl.

    Returns None if it is not set.
    """
    return RunGit(['config', 'branch.%s.base-url' % self.GetBranch()],
                  error_ok=True).strip()

  def GetRemoteUrl(self):
    """Return the configured remote URL, e.g. 'git://example.org/foo.git/'.

    Returns None if there is no remote.
    """
    remote = self.GetRemote()
    return RunGit(['config', 'remote.%s.url' % remote], error_ok=True).strip()

  def GetIssue(self):
    """Returns the issue number as a int or None if not set."""
    if not self.has_issue:
      issue = RunGit(['config', self._IssueSetting()], error_ok=True).strip()
      if issue:
        self.issue = int(issue)
      else:
        self.issue = None
      self.has_issue = True
    return self.issue

  def GetRietveldServer(self):
    if not self.rietveld_server:
      # If we're on a branch then get the server potentially associated
      # with that branch.
      if self.GetIssue():
        self.rietveld_server = gclient_utils.UpgradeToHttps(RunGit(
            ['config', self._RietveldServer()], error_ok=True).strip())
      if not self.rietveld_server:
        self.rietveld_server = settings.GetDefaultServerUrl()
    return self.rietveld_server

  def GetIssueURL(self):
    """Get the URL for a particular issue."""
    return '%s/%s' % (self.GetRietveldServer(), self.GetIssue())

  def GetDescription(self, pretty=False):
    if not self.has_description:
      if self.GetIssue():
        issue = self.GetIssue()
        try:
          self.description = self.RpcServer().get_description(issue).strip()
        except urllib2.HTTPError, e:
          if e.code == 404:
            DieWithError(
                ('\nWhile fetching the description for issue %d, received a '
                 '404 (not found)\n'
                 'error. It is likely that you deleted this '
                 'issue on the server. If this is the\n'
                 'case, please run\n\n'
                 '    git cl issue 0\n\n'
                 'to clear the association with the deleted issue. Then run '
                 'this command again.') % issue)
          else:
            DieWithError(
                '\nFailed to fetch issue description. HTTP error ' + e.code)
      self.has_description = True
    if pretty:
      wrapper = textwrap.TextWrapper()
      wrapper.initial_indent = wrapper.subsequent_indent = '  '
      return wrapper.fill(self.description)
    return self.description

  def GetPatchset(self):
    """Returns the patchset number as a int or None if not set."""
    if not self.has_patchset:
      patchset = RunGit(['config', self._PatchsetSetting()],
                        error_ok=True).strip()
      if patchset:
        self.patchset = int(patchset)
      else:
        self.patchset = None
      self.has_patchset = True
    return self.patchset

  def SetPatchset(self, patchset):
    """Set this branch's patchset.  If patchset=0, clears the patchset."""
    if patchset:
      RunGit(['config', self._PatchsetSetting(), str(patchset)])
    else:
      RunGit(['config', '--unset', self._PatchsetSetting()],
             stderr=subprocess2.PIPE, error_ok=True)
    self.has_patchset = False

  def GetPatchSetDiff(self, issue):
    patchset = self.RpcServer().get_issue_properties(
        int(issue), False)['patchsets'][-1]
    return self.RpcServer().get(
        '/download/issue%s_%s.diff' % (issue, patchset))

  def SetIssue(self, issue):
    """Set this branch's issue.  If issue=0, clears the issue."""
    if issue:
      RunGit(['config', self._IssueSetting(), str(issue)])
      if self.rietveld_server:
        RunGit(['config', self._RietveldServer(), self.rietveld_server])
    else:
      RunGit(['config', '--unset', self._IssueSetting()])
      self.SetPatchset(0)
    self.has_issue = False

  def GetChange(self, upstream_branch, author):
    root = RunCommand(['git', 'rev-parse', '--show-cdup']).strip() or '.'
    absroot = os.path.abspath(root)

    # We use the sha1 of HEAD as a name of this change.
    name = RunCommand(['git', 'rev-parse', 'HEAD']).strip()
    # Need to pass a relative path for msysgit.
    try:
      files = scm.GIT.CaptureStatus([root], '.', upstream_branch)
    except subprocess2.CalledProcessError:
      DieWithError(
          ('\nFailed to diff against upstream branch %s!\n\n'
           'This branch probably doesn\'t exist anymore. To reset the\n'
           'tracking branch, please run\n'
           '    git branch --set-upstream %s trunk\n'
           'replacing trunk with origin/master or the relevant branch') %
          (upstream_branch, self.GetBranch()))

    issue = self.GetIssue()
    patchset = self.GetPatchset()
    if issue:
      description = self.GetDescription()
    else:
      # If the change was never uploaded, use the log messages of all commits
      # up to the branch point, as git cl upload will prefill the description
      # with these log messages.
      description = RunCommand(['git', 'log', '--pretty=format:%s%n%n%b',
                                '%s...' % (upstream_branch)]).strip()

    if not author:
      author = RunGit(['config', 'user.email']).strip() or None
    return presubmit_support.GitChange(
        name,
        description,
        absroot,
        files,
        issue,
        patchset,
        author)

  def RunHook(self, committing, upstream_branch, may_prompt, verbose, author):
    """Calls sys.exit() if the hook fails; returns a HookResults otherwise."""
    change = self.GetChange(upstream_branch, author)

    # Apply watchlists on upload.
    if not committing:
      watchlist = watchlists.Watchlists(change.RepositoryRoot())
      files = [f.LocalPath() for f in change.AffectedFiles()]
      self.SetWatchers(watchlist.GetWatchersForPaths(files))

    try:
      return presubmit_support.DoPresubmitChecks(change, committing,
          verbose=verbose, output_stream=sys.stdout, input_stream=sys.stdin,
          default_presubmit=None, may_prompt=may_prompt,
          rietveld_obj=self.RpcServer())
    except presubmit_support.PresubmitFailure, e:
      DieWithError(
          ('%s\nMaybe your depot_tools is out of date?\n'
           'If all fails, contact maruel@') % e)

  def CloseIssue(self):
    """Updates the description and closes the issue."""
    issue = self.GetIssue()
    self.RpcServer().update_description(issue, self.description)
    return self.RpcServer().close_issue(issue)

  def SetFlag(self, flag, value):
    """Patchset must match."""
    if not self.GetPatchset():
      DieWithError('The patchset needs to match. Send another patchset.')
    try:
      return self.RpcServer().set_flag(
          self.GetIssue(), self.GetPatchset(), flag, value)
    except urllib2.HTTPError, e:
      if e.code == 404:
        DieWithError('The issue %s doesn\'t exist.' % self.GetIssue())
      if e.code == 403:
        DieWithError(
            ('Access denied to issue %s. Maybe the patchset %s doesn\'t '
             'match?') % (self.GetIssue(), self.GetPatchset()))
      raise

  def RpcServer(self):
    """Returns an upload.RpcServer() to access this review's rietveld instance.
    """
    if not self._rpc_server:
      self._rpc_server = rietveld.Rietveld(self.GetRietveldServer(),
                                           None, None)
    return self._rpc_server

  def _IssueSetting(self):
    """Return the git setting that stores this change's issue."""
    return 'branch.%s.rietveldissue' % self.GetBranch()

  def _PatchsetSetting(self):
    """Return the git setting that stores this change's most recent patchset."""
    return 'branch.%s.rietveldpatchset' % self.GetBranch()

  def _RietveldServer(self):
    """Returns the git setting that stores this change's rietveld server."""
    return 'branch.%s.rietveldserver' % self.GetBranch()


def GetCodereviewSettingsInteractively():
  """Prompt the user for settings."""
  # TODO(ukai): ask code review system is rietveld or gerrit?
  server = settings.GetDefaultServerUrl(error_ok=True)
  prompt = 'Rietveld server (host[:port])'
  prompt += ' [%s]' % (server or DEFAULT_SERVER)
  newserver = ask_for_data(prompt + ':')
  if not server and not newserver:
    newserver = DEFAULT_SERVER
  if newserver:
    newserver = gclient_utils.UpgradeToHttps(newserver)
    if newserver != server:
      RunGit(['config', 'rietveld.server', newserver])

  def SetProperty(initial, caption, name, is_url):
    prompt = caption
    if initial:
      prompt += ' ("x" to clear) [%s]' % initial
    new_val = ask_for_data(prompt + ':')
    if new_val == 'x':
      RunGit(['config', '--unset-all', 'rietveld.' + name], error_ok=True)
    elif new_val:
      if is_url:
        new_val = gclient_utils.UpgradeToHttps(new_val)
      if new_val != initial:
        RunGit(['config', 'rietveld.' + name, new_val])

  SetProperty(settings.GetDefaultCCList(), 'CC list', 'cc', False)
  SetProperty(settings.GetTreeStatusUrl(error_ok=True), 'Tree status URL',
              'tree-status-url', False)
  SetProperty(settings.GetViewVCUrl(), 'ViewVC URL', 'viewvc-url', True)

  # TODO: configure a default branch to diff against, rather than this
  # svn-based hackery.


class ChangeDescription(object):
  """Contains a parsed form of the change description."""
  def __init__(self, log_desc, reviewers):
    self.log_desc = log_desc
    self.reviewers = reviewers
    self.description = self.log_desc

  def Prompt(self):
    content = """# Enter a description of the change.
# This will displayed on the codereview site.
# The first line will also be used as the subject of the review.
"""
    content += self.description
    if ('\nR=' not in self.description and
        '\nTBR=' not in self.description and
        self.reviewers):
      content += '\nR=' + self.reviewers
    if '\nBUG=' not in self.description:
      content += '\nBUG='
    content = content.rstrip('\n') + '\n'
    content = gclient_utils.RunEditor(content, True)
    if not content:
      DieWithError('Running editor failed')
    content = re.compile(r'^#.*$', re.MULTILINE).sub('', content).strip()
    if not content.strip():
      DieWithError('No CL description, aborting')
    self.description = content

  def ParseDescription(self):
    """Updates the list of reviewers and subject from the description."""
    self.description = self.description.strip('\n') + '\n'
    # Retrieves all reviewer lines
    regexp = re.compile(r'^\s*(TBR|R)=(.+)$', re.MULTILINE)
    reviewers = ','.join(
        i.group(2).strip() for i in regexp.finditer(self.description))
    if reviewers:
      self.reviewers = reviewers

  def IsEmpty(self):
    return not self.description


def FindCodereviewSettingsFile(filename='codereview.settings'):
  """Finds the given file starting in the cwd and going up.

  Only looks up to the top of the repository unless an
  'inherit-review-settings-ok' file exists in the root of the repository.
  """
  inherit_ok_file = 'inherit-review-settings-ok'
  cwd = os.getcwd()
  root = os.path.abspath(RunGit(['rev-parse', '--show-cdup']).strip())
  if os.path.isfile(os.path.join(root, inherit_ok_file)):
    root = '/'
  while True:
    if filename in os.listdir(cwd):
      if os.path.isfile(os.path.join(cwd, filename)):
        return open(os.path.join(cwd, filename))
    if cwd == root:
      break
    cwd = os.path.dirname(cwd)


def LoadCodereviewSettingsFromFile(fileobj):
  """Parse a codereview.settings file and updates hooks."""
  keyvals = gclient_utils.ParseCodereviewSettingsContent(fileobj.read())

  def SetProperty(name, setting, unset_error_ok=False):
    fullname = 'rietveld.' + name
    if setting in keyvals:
      RunGit(['config', fullname, keyvals[setting]])
    else:
      RunGit(['config', '--unset-all', fullname], error_ok=unset_error_ok)

  SetProperty('server', 'CODE_REVIEW_SERVER')
  # Only server setting is required. Other settings can be absent.
  # In that case, we ignore errors raised during option deletion attempt.
  SetProperty('cc', 'CC_LIST', unset_error_ok=True)
  SetProperty('tree-status-url', 'STATUS', unset_error_ok=True)
  SetProperty('viewvc-url', 'VIEW_VC', unset_error_ok=True)

  if 'GERRIT_HOST' in keyvals and 'GERRIT_PORT' in keyvals:
    RunGit(['config', 'gerrit.host', keyvals['GERRIT_HOST']])
    RunGit(['config', 'gerrit.port', keyvals['GERRIT_PORT']])

  if 'PUSH_URL_CONFIG' in keyvals and 'ORIGIN_URL_CONFIG' in keyvals:
    #should be of the form
    #PUSH_URL_CONFIG: url.ssh://gitrw.chromium.org.pushinsteadof
    #ORIGIN_URL_CONFIG: http://src.chromium.org/git
    RunGit(['config', keyvals['PUSH_URL_CONFIG'],
            keyvals['ORIGIN_URL_CONFIG']])


def urlretrieve(source, destination):
  """urllib is broken for SSL connections via a proxy therefore we
  can't use urllib.urlretrieve()."""
  with open(destination, 'w') as f:
    f.write(urllib2.urlopen(source).read())


def DownloadHooks(force):
  """downloads hooks

  Args:
    force: True to update hooks. False to install hooks if not present.
  """
  if not settings.GetIsGerrit():
    return
  server_url = settings.GetDefaultServerUrl()
  src = '%s/tools/hooks/commit-msg' % server_url
  dst = os.path.join(settings.GetRoot(), '.git', 'hooks', 'commit-msg')
  if not os.access(dst, os.X_OK):
    if os.path.exists(dst):
      if not force:
        return
      os.remove(dst)
    try:
      urlretrieve(src, dst)
      os.chmod(dst, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except Exception:
      if os.path.exists(dst):
        os.remove(dst)
      DieWithError('\nFailed to download hooks from %s' % src)


@usage('[repo root containing codereview.settings]')
def CMDconfig(parser, args):
  """edit configuration for this tree"""

  _, args = parser.parse_args(args)
  if len(args) == 0:
    GetCodereviewSettingsInteractively()
    DownloadHooks(True)
    return 0

  url = args[0]
  if not url.endswith('codereview.settings'):
    url = os.path.join(url, 'codereview.settings')

  # Load code review settings and download hooks (if available).
  LoadCodereviewSettingsFromFile(urllib2.urlopen(url))
  DownloadHooks(True)
  return 0


def CMDbaseurl(parser, args):
  """get or set base-url for this branch"""
  branchref = RunGit(['symbolic-ref', 'HEAD']).strip()
  branch = ShortBranchName(branchref)
  _, args = parser.parse_args(args)
  if not args:
    print("Current base-url:")
    return RunGit(['config', 'branch.%s.base-url' % branch],
                  error_ok=False).strip()
  else:
    print("Setting base-url to %s" % args[0])
    return RunGit(['config', 'branch.%s.base-url' % branch, args[0]],
                  error_ok=False).strip()


def CMDstatus(parser, args):
  """show status of changelists"""
  parser.add_option('--field',
                    help='print only specific field (desc|id|patch|url)')
  (options, args) = parser.parse_args(args)

  # TODO: maybe make show_branches a flag if necessary.
  show_branches = not options.field

  if show_branches:
    branches = RunGit(['for-each-ref', '--format=%(refname)', 'refs/heads'])
    if branches:
      print 'Branches associated with reviews:'
      changes = (Changelist(branchref=b) for b in branches.splitlines())
      branches = dict((cl.GetBranch(), cl.GetIssue()) for cl in changes)
      alignment = max(5, max(len(b) for b in branches))
      for branch in sorted(branches):
        print "  %*s: %s" % (alignment, branch, branches[branch])

  cl = Changelist()
  if options.field:
    if options.field.startswith('desc'):
      print cl.GetDescription()
    elif options.field == 'id':
      issueid = cl.GetIssue()
      if issueid:
        print issueid
    elif options.field == 'patch':
      patchset = cl.GetPatchset()
      if patchset:
        print patchset
    elif options.field == 'url':
      url = cl.GetIssueURL()
      if url:
        print url
  else:
    print
    print 'Current branch:',
    if not cl.GetIssue():
      print 'no issue assigned.'
      return 0
    print cl.GetBranch()
    print 'Issue number: %s (%s)' % (cl.GetIssue(), cl.GetIssueURL())
    print 'Issue description:'
    print cl.GetDescription(pretty=True)
  return 0


@usage('[issue_number]')
def CMDissue(parser, args):
  """Set or display the current code review issue number.

  Pass issue number 0 to clear the current issue.
"""
  _, args = parser.parse_args(args)

  cl = Changelist()
  if len(args) > 0:
    try:
      issue = int(args[0])
    except ValueError:
      DieWithError('Pass a number to set the issue or none to list it.\n'
          'Maybe you want to run git cl status?')
    cl.SetIssue(issue)
  print 'Issue number: %s (%s)' % (cl.GetIssue(), cl.GetIssueURL())
  return 0


def CMDcomments(parser, args):
  """show review comments of the current changelist"""
  (_, args) = parser.parse_args(args)
  if args:
    parser.error('Unsupported argument: %s' % args)

  cl = Changelist()
  if cl.GetIssue():
    data = cl.RpcServer().get_issue_properties(cl.GetIssue(), True)
    for message in sorted(data['messages'], key=lambda x: x['date']):
      print '\n%s  %s' % (message['date'].split('.', 1)[0], message['sender'])
      if message['text'].strip():
        print '\n'.join('  ' + l for l in message['text'].splitlines())
  return 0


def CreateDescriptionFromLog(args):
  """Pulls out the commit log to use as a base for the CL description."""
  log_args = []
  if len(args) == 1 and not args[0].endswith('.'):
    log_args = [args[0] + '..']
  elif len(args) == 1 and args[0].endswith('...'):
    log_args = [args[0][:-1]]
  elif len(args) == 2:
    log_args = [args[0] + '..' + args[1]]
  else:
    log_args = args[:]  # Hope for the best!
  return RunGit(['log', '--pretty=format:%s\n\n%b'] + log_args)


def CMDpresubmit(parser, args):
  """run presubmit tests on the current changelist"""
  parser.add_option('--upload', action='store_true',
                    help='Run upload hook instead of the push/dcommit hook')
  parser.add_option('--force', action='store_true',
                    help='Run checks even if tree is dirty')
  (options, args) = parser.parse_args(args)

  # Make sure index is up-to-date before running diff-index.
  RunGit(['update-index', '--refresh', '-q'], error_ok=True)
  if not options.force and RunGit(['diff-index', 'HEAD']):
    # TODO(maruel): Is this really necessary?
    print ('Cannot presubmit with a dirty tree.\n'
          'You must commit locally first (or use --force).')
    return 1

  cl = Changelist()
  if args:
    base_branch = args[0]
  else:
    # Default to diffing against the "upstream" branch.
    base_branch = cl.GetUpstreamBranch()

  cl.RunHook(committing=not options.upload, upstream_branch=base_branch,
             may_prompt=False, verbose=options.verbose,
             author=None)
  return 0


def GerritUpload(options, args, cl):
  """upload the current branch to gerrit."""
  # We assume the remote called "origin" is the one we want.
  # It is probably not worthwhile to support different workflows.
  remote = 'origin'
  branch = 'master'
  if options.target_branch:
    branch = options.target_branch

  log_desc = options.message or CreateDescriptionFromLog(args)
  if options.reviewers:
    log_desc += '\nR=' + options.reviewers
  change_desc = ChangeDescription(log_desc, options.reviewers)
  change_desc.ParseDescription()
  if change_desc.IsEmpty():
    print "Description is empty; aborting."
    return 1

  receive_options = []
  cc = cl.GetCCList().split(',')
  if options.cc:
    cc += options.cc.split(',')
  cc = filter(None, cc)
  if cc:
    receive_options += ['--cc=' + email for email in cc]
  if change_desc.reviewers:
    reviewers = filter(None, change_desc.reviewers.split(','))
    if reviewers:
      receive_options += ['--reviewer=' + email for email in reviewers]

  git_command = ['push']
  if receive_options:
    git_command.append('--receive-pack=git receive-pack %s' %
                       ' '.join(receive_options))
  git_command += [remote, 'HEAD:refs/for/' + branch]
  RunGit(git_command)
  # TODO(ukai): parse Change-Id: and set issue number?
  return 0


def RietveldUpload(options, args, cl):
  """upload the patch to rietveld."""
  upload_args = ['--assume_yes']  # Don't ask about untracked files.
  upload_args.extend(['--server', cl.GetRietveldServer()])
  if options.emulate_svn_auto_props:
    upload_args.append('--emulate_svn_auto_props')

  change_desc = None

  if cl.GetIssue():
    if options.title:
      upload_args.extend(['--title', options.title])
    elif options.message:
      # TODO(rogerta): for now, the -m option will also set the --title option
      # for upload.py.  Soon this will be changed to set the --message option.
      # Will wait until people are used to typing -t instead of -m.
      upload_args.extend(['--title', options.message])
    upload_args.extend(['--issue', str(cl.GetIssue())])
    print ("This branch is associated with issue %s. "
           "Adding patch to that issue." % cl.GetIssue())
  else:
    if options.title:
      upload_args.extend(['--title', options.title])
    message = options.message or CreateDescriptionFromLog(args)
    change_desc = ChangeDescription(message, options.reviewers)
    if not options.force:
      change_desc.Prompt()
    change_desc.ParseDescription()

    if change_desc.IsEmpty():
      print "Description is empty; aborting."
      return 1

    upload_args.extend(['--message', change_desc.description])
    if change_desc.reviewers:
      upload_args.extend(['--reviewers', change_desc.reviewers])
    if options.send_mail:
      if not change_desc.reviewers:
        DieWithError("Must specify reviewers to send email.")
      upload_args.append('--send_mail')
    cc = ','.join(filter(None, (cl.GetCCList(), options.cc)))
    if cc:
      upload_args.extend(['--cc', cc])

  # Include the upstream repo's URL in the change -- this is useful for
  # projects that have their source spread across multiple repos.
  remote_url = cl.GetGitBaseUrlFromConfig()
  if not remote_url:
    if settings.GetIsGitSvn():
      # URL is dependent on the current directory.
      data = RunGit(['svn', 'info'], cwd=settings.GetRoot())
      if data:
        keys = dict(line.split(': ', 1) for line in data.splitlines()
                    if ': ' in line)
        remote_url = keys.get('URL', None)
    else:
      if cl.GetRemoteUrl() and '/' in cl.GetUpstreamBranch():
        remote_url = (cl.GetRemoteUrl() + '@'
                      + cl.GetUpstreamBranch().split('/')[-1])
  if remote_url:
    upload_args.extend(['--base_url', remote_url])

  try:
    issue, patchset = upload.RealMain(['upload'] + upload_args + args)
  except KeyboardInterrupt:
    sys.exit(1)
  except:
    # If we got an exception after the user typed a description for their
    # change, back up the description before re-raising.
    if change_desc:
      backup_path = os.path.expanduser(DESCRIPTION_BACKUP_FILE)
      print '\nGot exception while uploading -- saving description to %s\n' \
          % backup_path
      backup_file = open(backup_path, 'w')
      backup_file.write(change_desc.description)
      backup_file.close()
    raise

  if not cl.GetIssue():
    cl.SetIssue(issue)
  cl.SetPatchset(patchset)

  if options.use_commit_queue:
    cl.SetFlag('commit', '1')
  return 0


@usage('[args to "git diff"]')
def CMDupload(parser, args):
  """upload the current changelist to codereview"""
  parser.add_option('--bypass-hooks', action='store_true', dest='bypass_hooks',
                    help='bypass upload presubmit hook')
  parser.add_option('-f', action='store_true', dest='force',
                    help="force yes to questions (don't prompt)")
  parser.add_option('-m', dest='message', help='message for patchset')
  parser.add_option('-t', dest='title', help='title for patchset')
  parser.add_option('-r', '--reviewers',
                    help='reviewer email addresses')
  parser.add_option('--cc',
                    help='cc email addresses')
  parser.add_option('--send-mail', action='store_true',
                    help='send email to reviewer immediately')
  parser.add_option("--emulate_svn_auto_props", action="store_true",
                    dest="emulate_svn_auto_props",
                    help="Emulate Subversion's auto properties feature.")
  parser.add_option('-c', '--use-commit-queue', action='store_true',
                    help='tell the commit queue to commit this patchset')
  if settings.GetIsGerrit():
    parser.add_option('--target_branch', dest='target_branch', default='master',
                      help='target branch to upload')
  (options, args) = parser.parse_args(args)

  # Print warning if the user used the -m/--message argument.  This will soon
  # change to -t/--title.
  if options.message:
    print >> sys.stderr, (
        '\nWARNING: Use -t or --title to set the title of the patchset.\n'
        'In the near future, -m or --message will send a message instead.\n'
        'See http://goo.gl/JGg0Z for details.\n')

  # Make sure index is up-to-date before running diff-index.
  RunGit(['update-index', '--refresh', '-q'], error_ok=True)
  if RunGit(['diff-index', 'HEAD']):
    print 'Cannot upload with a dirty tree.  You must commit locally first.'
    return 1

  cl = Changelist()
  if args:
    # TODO(ukai): is it ok for gerrit case?
    base_branch = args[0]
  else:
    # Default to diffing against the "upstream" branch.
    base_branch = cl.GetUpstreamBranch()
    args = [base_branch + "..."]

  if not options.bypass_hooks:
    hook_results = cl.RunHook(committing=False, upstream_branch=base_branch,
                              may_prompt=not options.force,
                              verbose=options.verbose,
                              author=None)
    if not hook_results.should_continue():
      return 1
    if not options.reviewers and hook_results.reviewers:
      options.reviewers = hook_results.reviewers

  print_stats(args)
  if settings.GetIsGerrit():
    return GerritUpload(options, args, cl)
  return RietveldUpload(options, args, cl)


def IsSubmoduleMergeCommit(ref):
  # When submodules are added to the repo, we expect there to be a single
  # non-git-svn merge commit at remote HEAD with a signature comment.
  pattern = '^SVN changes up to revision [0-9]*$'
  cmd = ['rev-list', '--merges', '--grep=%s' % pattern, '%s^!' % ref]
  return RunGit(cmd) != ''


def SendUpstream(parser, args, cmd):
  """Common code for CmdPush and CmdDCommit

  Squashed commit into a single.
  Updates changelog with metadata (e.g. pointer to review).
  Pushes/dcommits the code upstream.
  Updates review and closes.
  """
  parser.add_option('--bypass-hooks', action='store_true', dest='bypass_hooks',
                    help='bypass upload presubmit hook')
  parser.add_option('-m', dest='message',
                    help="override review description")
  parser.add_option('-f', action='store_true', dest='force',
                    help="force yes to questions (don't prompt)")
  parser.add_option('-c', dest='contributor',
                    help="external contributor for patch (appended to " +
                         "description and used as author for git). Should be " +
                         "formatted as 'First Last <email@example.com>'")
  (options, args) = parser.parse_args(args)
  cl = Changelist()

  if not args or cmd == 'push':
    # Default to merging against our best guess of the upstream branch.
    args = [cl.GetUpstreamBranch()]

  if options.contributor:
    if not re.match('^.*\s<\S+@\S+>$', options.contributor):
      print "Please provide contibutor as 'First Last <email@example.com>'"
      return 1

  base_branch = args[0]
  base_has_submodules = IsSubmoduleMergeCommit(base_branch)

  # Make sure index is up-to-date before running diff-index.
  RunGit(['update-index', '--refresh', '-q'], error_ok=True)
  if RunGit(['diff-index', 'HEAD']):
    print 'Cannot %s with a dirty tree.  You must commit locally first.' % cmd
    return 1

  # This rev-list syntax means "show all commits not in my branch that
  # are in base_branch".
  upstream_commits = RunGit(['rev-list', '^' + cl.GetBranchRef(),
                             base_branch]).splitlines()
  if upstream_commits:
    print ('Base branch "%s" has %d commits '
           'not in this branch.' % (base_branch, len(upstream_commits)))
    print 'Run "git merge %s" before attempting to %s.' % (base_branch, cmd)
    return 1

  # This is the revision `svn dcommit` will commit on top of.
  svn_head = RunGit(['log', '--grep=^git-svn-id:', '-1',
                     '--pretty=format:%H'])

  if cmd == 'dcommit':
    # If the base_head is a submodule merge commit, the first parent of the
    # base_head should be a git-svn commit, which is what we're interested in.
    base_svn_head = base_branch
    if base_has_submodules:
      base_svn_head += '^1'

    extra_commits = RunGit(['rev-list', '^' + svn_head, base_svn_head])
    if extra_commits:
      print ('This branch has %d additional commits not upstreamed yet.'
             % len(extra_commits.splitlines()))
      print ('Upstream "%s" or rebase this branch on top of the upstream trunk '
             'before attempting to %s.' % (base_branch, cmd))
      return 1

  if not options.bypass_hooks:
    author = None
    if options.contributor:
      author = re.search(r'\<(.*)\>', options.contributor).group(1)
    hook_results = cl.RunHook(
        committing=True,
        upstream_branch=base_branch,
        may_prompt=not options.force,
        verbose=options.verbose,
        author=author)
    if not hook_results.should_continue():
      return 1

    if cmd == 'dcommit':
      # Check the tree status if the tree status URL is set.
      status = GetTreeStatus()
      if 'closed' == status:
        print('The tree is closed.  Please wait for it to reopen. Use '
              '"git cl dcommit --bypass-hooks" to commit on a closed tree.')
        return 1
      elif 'unknown' == status:
        print('Unable to determine tree status.  Please verify manually and '
              'use "git cl dcommit --bypass-hooks" to commit on a closed tree.')
  else:
    breakpad.SendStack(
        'GitClHooksBypassedCommit',
        'Issue %s/%s bypassed hook when committing' %
        (cl.GetRietveldServer(), cl.GetIssue()),
        verbose=False)

  description = options.message
  if not description and cl.GetIssue():
    description = cl.GetDescription()

  if not description:
    if not cl.GetIssue() and options.bypass_hooks:
      description = CreateDescriptionFromLog([base_branch])
    else:
      print 'No description set.'
      print 'Visit %s/edit to set it.' % (cl.GetIssueURL())
      return 1

  if cl.GetIssue():
    description += "\n\nReview URL: %s" % cl.GetIssueURL()

  if options.contributor:
    description += "\nPatch from %s." % options.contributor
  print 'Description:', repr(description)

  branches = [base_branch, cl.GetBranchRef()]
  if not options.force:
    print_stats(branches)
    ask_for_data('About to commit; enter to confirm.')

  # We want to squash all this branch's commits into one commit with the proper
  # description. We do this by doing a "reset --soft" to the base branch (which
  # keeps the working copy the same), then dcommitting that.  If origin/master
  # has a submodule merge commit, we'll also need to cherry-pick the squashed
  # commit onto a branch based on the git-svn head.
  MERGE_BRANCH = 'git-cl-commit'
  CHERRY_PICK_BRANCH = 'git-cl-cherry-pick'
  # Delete the branches if they exist.
  for branch in [MERGE_BRANCH, CHERRY_PICK_BRANCH]:
    showref_cmd = ['show-ref', '--quiet', '--verify', 'refs/heads/%s' % branch]
    result = RunGitWithCode(showref_cmd)
    if result[0] == 0:
      RunGit(['branch', '-D', branch])

  # We might be in a directory that's present in this branch but not in the
  # trunk.  Move up to the top of the tree so that git commands that expect a
  # valid CWD won't fail after we check out the merge branch.
  rel_base_path = RunGit(['rev-parse', '--show-cdup']).strip()
  if rel_base_path:
    os.chdir(rel_base_path)

  # Stuff our change into the merge branch.
  # We wrap in a try...finally block so if anything goes wrong,
  # we clean up the branches.
  retcode = -1
  try:
    RunGit(['checkout', '-q', '-b', MERGE_BRANCH])
    RunGit(['reset', '--soft', base_branch])
    if options.contributor:
      RunGit(['commit', '--author', options.contributor, '-m', description])
    else:
      RunGit(['commit', '-m', description])
    if base_has_submodules:
      cherry_pick_commit = RunGit(['rev-list', 'HEAD^!']).rstrip()
      RunGit(['branch', CHERRY_PICK_BRANCH, svn_head])
      RunGit(['checkout', CHERRY_PICK_BRANCH])
      RunGit(['cherry-pick', cherry_pick_commit])
    if cmd == 'push':
      # push the merge branch.
      remote, branch = cl.FetchUpstreamTuple()
      retcode, output = RunGitWithCode(
          ['push', '--porcelain', remote, 'HEAD:%s' % branch])
      logging.debug(output)
    else:
      # dcommit the merge branch.
      retcode, output = RunGitWithCode(['svn', 'dcommit',
                                        '--no-rebase', '--rmdir'])
  finally:
    # And then swap back to the original branch and clean up.
    RunGit(['checkout', '-q', cl.GetBranch()])
    RunGit(['branch', '-D', MERGE_BRANCH])
    if base_has_submodules:
      RunGit(['branch', '-D', CHERRY_PICK_BRANCH])

  if cl.GetIssue():
    if cmd == 'dcommit' and 'Committed r' in output:
      revision = re.match('.*?\nCommitted r(\\d+)', output, re.DOTALL).group(1)
    elif cmd == 'push' and retcode == 0:
      match = (re.match(r'.*?([a-f0-9]{7})\.\.([a-f0-9]{7})$', l)
               for l in output.splitlines(False))
      match = filter(None, match)
      if len(match) != 1:
        DieWithError("Couldn't parse ouput to extract the committed hash:\n%s" %
            output)
      revision = match[0].group(2)
    else:
      return 1
    viewvc_url = settings.GetViewVCUrl()
    if viewvc_url and revision:
      cl.description += ('\n\nCommitted: ' + viewvc_url + revision)
    print ('Closing issue '
           '(you may be prompted for your codereview password)...')
    cl.CloseIssue()
    cl.SetIssue(0)

  if retcode == 0:
    hook = POSTUPSTREAM_HOOK_PATTERN % cmd
    if os.path.isfile(hook):
      RunCommand([hook, base_branch], error_ok=True)

  return 0


@usage('[upstream branch to apply against]')
def CMDdcommit(parser, args):
  """commit the current changelist via git-svn"""
  if not settings.GetIsGitSvn():
    message = """This doesn't appear to be an SVN repository.
If your project has a git mirror with an upstream SVN master, you probably need
to run 'git svn init', see your project's git mirror documentation.
If your project has a true writeable upstream repository, you probably want
to run 'git cl push' instead.
Choose wisely, if you get this wrong, your commit might appear to succeed but
will instead be silently ignored."""
    print(message)
    ask_for_data('[Press enter to dcommit or ctrl-C to quit]')
  return SendUpstream(parser, args, 'dcommit')


@usage('[upstream branch to apply against]')
def CMDpush(parser, args):
  """commit the current changelist via git"""
  if settings.GetIsGitSvn():
    print('This appears to be an SVN repository.')
    print('Are you sure you didn\'t mean \'git cl dcommit\'?')
    ask_for_data('[Press enter to push or ctrl-C to quit]')
  return SendUpstream(parser, args, 'push')


@usage('<patch url or issue id>')
def CMDpatch(parser, args):
  """patch in a code review"""
  parser.add_option('-b', dest='newbranch',
                    help='create a new branch off trunk for the patch')
  parser.add_option('-f', action='store_true', dest='force',
                    help='with -b, clobber any existing branch')
  parser.add_option('--reject', action='store_true', dest='reject',
                    help='allow failed patches and spew .rej files')
  parser.add_option('-n', '--no-commit', action='store_true', dest='nocommit',
                    help="don't commit after patch applies")
  (options, args) = parser.parse_args(args)
  if len(args) != 1:
    parser.print_help()
    return 1
  issue_arg = args[0]

  # TODO(maruel): Use apply_issue.py
  # TODO(ukai): use gerrit-cherry-pick for gerrit repository?

  if issue_arg.isdigit():
    # Input is an issue id.  Figure out the URL.
    issue = int(issue_arg)
    patch_data = Changelist().GetPatchSetDiff(issue)
  else:
    # Assume it's a URL to the patch. Default to https.
    issue_url = gclient_utils.UpgradeToHttps(issue_arg)
    match = re.match(r'.*?/issue(\d+)_\d+.diff', issue_url)
    if not match:
      DieWithError('Must pass an issue ID or full URL for '
          '\'Download raw patch set\'')
    issue = int(match.group(1))
    patch_data = urllib2.urlopen(issue_arg).read()

  if options.newbranch:
    if options.force:
      RunGit(['branch', '-D', options.newbranch],
          stderr=subprocess2.PIPE, error_ok=True)
    RunGit(['checkout', '-b', options.newbranch,
            Changelist().GetUpstreamBranch()])

  # Switch up to the top-level directory, if necessary, in preparation for
  # applying the patch.
  top = RunGit(['rev-parse', '--show-cdup']).strip()
  if top:
    os.chdir(top)

  # Git patches have a/ at the beginning of source paths.  We strip that out
  # with a sed script rather than the -p flag to patch so we can feed either
  # Git or svn-style patches into the same apply command.
  # re.sub() should be used but flags=re.MULTILINE is only in python 2.7.
  try:
    patch_data = subprocess2.check_output(
        ['sed', '-e', 's|^--- a/|--- |; s|^+++ b/|+++ |'], stdin=patch_data)
  except subprocess2.CalledProcessError:
    DieWithError('Git patch mungling failed.')
  logging.info(patch_data)
  # We use "git apply" to apply the patch instead of "patch" so that we can
  # pick up file adds.
  # The --index flag means: also insert into the index (so we catch adds).
  cmd = ['git', 'apply', '--index', '-p0']
  if options.reject:
    cmd.append('--reject')
  try:
    subprocess2.check_call(cmd, stdin=patch_data, stdout=subprocess2.VOID)
  except subprocess2.CalledProcessError:
    DieWithError('Failed to apply the patch')

  # If we had an issue, commit the current state and register the issue.
  if not options.nocommit:
    RunGit(['commit', '-m', 'patch from issue %s' % issue])
    cl = Changelist()
    cl.SetIssue(issue)
    print "Committed patch."
  else:
    print "Patch applied to index."
  return 0


def CMDrebase(parser, args):
  """rebase current branch on top of svn repo"""
  # Provide a wrapper for git svn rebase to help avoid accidental
  # git svn dcommit.
  # It's the only command that doesn't use parser at all since we just defer
  # execution to git-svn.
  return subprocess2.call(['git', 'svn', 'rebase'] + args)


def GetTreeStatus():
  """Fetches the tree status and returns either 'open', 'closed',
  'unknown' or 'unset'."""
  url = settings.GetTreeStatusUrl(error_ok=True)
  if url:
    status = urllib2.urlopen(url).read().lower()
    if status.find('closed') != -1 or status == '0':
      return 'closed'
    elif status.find('open') != -1 or status == '1':
      return 'open'
    return 'unknown'
  return 'unset'


def GetTreeStatusReason():
  """Fetches the tree status from a json url and returns the message
  with the reason for the tree to be opened or closed."""
  url = settings.GetTreeStatusUrl()
  json_url = urlparse.urljoin(url, '/current?format=json')
  connection = urllib2.urlopen(json_url)
  status = json.loads(connection.read())
  connection.close()
  return status['message']


def CMDtree(parser, args):
  """show the status of the tree"""
  _, args = parser.parse_args(args)
  status = GetTreeStatus()
  if 'unset' == status:
    print 'You must configure your tree status URL by running "git cl config".'
    return 2

  print "The tree is %s" % status
  print
  print GetTreeStatusReason()
  if status != 'open':
    return 1
  return 0


def CMDtry(parser, args):
  """Triggers a try job through Rietveld."""
  group = optparse.OptionGroup(parser, "Try job options")
  group.add_option(
      "-b", "--bot", action="append",
      help=("IMPORTANT: specify ONE builder per --bot flag. Use it multiple "
            "times to specify multiple builders. ex: "
            "'-bwin_rel:ui_tests,webkit_unit_tests -bwin_layout'. See "
            "the try server waterfall for the builders name and the tests "
            "available. Can also be used to specify gtest_filter, e.g. "
            "-bwin_rel:base_unittests:ValuesTest.*Value"))
  group.add_option(
      "-r", "--revision",
      help="Revision to use for the try job; default: the "
           "revision will be determined by the try server; see "
           "its waterfall for more info")
  group.add_option(
      "-c", "--clobber", action="store_true", default=False,
      help="Force a clobber before building; e.g. don't do an "
           "incremental build")
  group.add_option(
      "--project",
      help="Override which project to use. Projects are defined "
           "server-side to define what default bot set to use")
  group.add_option(
      "-t", "--testfilter", action="append", default=[],
      help=("Apply a testfilter to all the selected builders. Unless the "
            "builders configurations are similar, use multiple "
            "--bot <builder>:<test> arguments."))
  group.add_option(
      "-n", "--name", help="Try job name; default to current branch name")
  parser.add_option_group(group)
  options, args = parser.parse_args(args)

  if args:
    parser.error('Unknown arguments: %s' % args)

  cl = Changelist()
  if not cl.GetIssue():
    parser.error('Need to upload first')

  if not options.name:
    options.name = cl.GetBranch()

  # Process --bot and --testfilter.
  if not options.bot:
    # Get try slaves from PRESUBMIT.py files if not specified.
    change = cl.GetChange(cl.GetUpstreamBranch(), None)
    options.bot = presubmit_support.DoGetTrySlaves(
        change,
        change.LocalPaths(),
        settings.GetRoot(),
        None,
        None,
        options.verbose,
        sys.stdout)
  if not options.bot:
    parser.error('No default try builder to try, use --bot')

  builders_and_tests = {}
  for bot in options.bot:
    if ':' in bot:
      builder, tests = bot.split(':', 1)
      builders_and_tests.setdefault(builder, []).extend(tests.split(','))
    elif ',' in bot:
      parser.error('Specify one bot per --bot flag')
    else:
      builders_and_tests.setdefault(bot, []).append('defaulttests')

  if options.testfilter:
    forced_tests = sum((t.split(',') for t in options.testfilter), [])
    builders_and_tests = dict(
      (b, forced_tests) for b, t in builders_and_tests.iteritems()
      if t != ['compile'])

  patchset = cl.GetPatchset()
  if not cl.GetPatchset():
    properties = cl.RpcServer().get_issue_properties(cl.GetIssue(), False)
    patchset = properties['patchsets'][-1]

  cl.RpcServer().trigger_try_jobs(
      cl.GetIssue(), patchset, options.name, options.clobber, options.revision,
      builders_and_tests)
  return 0


@usage('[new upstream branch]')
def CMDupstream(parser, args):
  """prints or sets the name of the upstream branch, if any"""
  _, args = parser.parse_args(args)
  if len(args) > 1:
    parser.error('Unrecognized args: %s' % ' '.join(args))
    return 0

  cl = Changelist()
  if args:
    # One arg means set upstream branch.
    RunGit(['branch', '--set-upstream', cl.GetBranch(), args[0]])
    cl = Changelist()
    print "Upstream branch set to " + cl.GetUpstreamBranch()
  else:
    print cl.GetUpstreamBranch()
  return 0


def CMDset_commit(parser, args):
  """set the commit bit"""
  _, args = parser.parse_args(args)
  if args:
    parser.error('Unrecognized args: %s' % ' '.join(args))
  cl = Changelist()
  cl.SetFlag('commit', '1')
  return 0


def Command(name):
  return getattr(sys.modules[__name__], 'CMD' + name, None)


def CMDhelp(parser, args):
  """print list of commands or help for a specific command"""
  _, args = parser.parse_args(args)
  if len(args) == 1:
    return main(args + ['--help'])
  parser.print_help()
  return 0


def GenUsage(parser, command):
  """Modify an OptParse object with the function's documentation."""
  obj = Command(command)
  more = getattr(obj, 'usage_more', '')
  if command == 'help':
    command = '<command>'
  else:
    # OptParser.description prefer nicely non-formatted strings.
    parser.description = re.sub('[\r\n ]{2,}', ' ', obj.__doc__)
  parser.set_usage('usage: %%prog %s [options] %s' % (command, more))


def main(argv):
  """Doesn't parse the arguments here, just find the right subcommand to
  execute."""
  if sys.hexversion < 0x02060000:
    print >> sys.stderr, (
        '\nYour python version %s is unsupported, please upgrade.\n' %
        sys.version.split(' ', 1)[0])
    return 2
  # Reload settings.
  global settings
  settings = Settings()

  # Do it late so all commands are listed.
  CMDhelp.usage_more = ('\n\nCommands are:\n' + '\n'.join([
      '  %-10s %s' % (fn[3:], Command(fn[3:]).__doc__.split('\n')[0].strip())
      for fn in dir(sys.modules[__name__]) if fn.startswith('CMD')]))

  # Create the option parse and add --verbose support.
  parser = optparse.OptionParser()
  parser.add_option(
      '-v', '--verbose', action='count', default=0,
      help='Use 2 times for more debugging info')
  old_parser_args = parser.parse_args
  def Parse(args):
    options, args = old_parser_args(args)
    if options.verbose >= 2:
      logging.basicConfig(level=logging.DEBUG)
    elif options.verbose:
      logging.basicConfig(level=logging.INFO)
    else:
      logging.basicConfig(level=logging.WARNING)
    return options, args
  parser.parse_args = Parse

  if argv:
    command = Command(argv[0])
    if command:
      # "fix" the usage and the description now that we know the subcommand.
      GenUsage(parser, argv[0])
      try:
        return command(parser, argv[1:])
      except urllib2.HTTPError, e:
        if e.code != 500:
          raise
        DieWithError(
            ('AppEngine is misbehaving and returned HTTP %d, again. Keep faith '
             'and retry or visit go/isgaeup.\n%s') % (e.code, str(e)))

  # Not a known command. Default to help.
  GenUsage(parser, 'help')
  return CMDhelp(parser, argv)


if __name__ == '__main__':
  fix_encoding.fix_encoding()
  sys.exit(main(sys.argv[1:]))
