#!/usr/bin/env python
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit tests for rietveld.py."""

import logging
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_support.patches_data import GIT, RAW

import patch
import rietveld


def _api(files):
  """Mock a rietveld api request."""
  return rietveld.json.dumps({'files': files})


def _file(
    status, is_binary=False, num_chunks=1, chunk_id=789, property_changes=''):
  """Mock a file in a rietveld api request."""
  return {
      'status': status,
      'is_binary': is_binary,
      'num_chunks': num_chunks,
      'id': chunk_id,
      'property_changes': property_changes,
  }


class RietveldTest(unittest.TestCase):
  def setUp(self):
    super(RietveldTest, self).setUp()
    # Access to a protected member XX of a client class
    # pylint: disable=W0212
    self.rietveld = rietveld.Rietveld('url', 'email', 'password')
    self.rietveld._send = self._rietveld_send
    self.requests = []

  def tearDown(self):
    self.assertEquals([], self.requests)
    super(RietveldTest, self).tearDown()

  def _rietveld_send(self, url, *args, **kwargs):
    self.assertTrue(self.requests, url)
    request = self.requests.pop(0)
    self.assertEquals(2, len(request))
    self.assertEquals(url, request[0])
    return request[1]

  def test_get_patch_empty(self):
    self.requests = [('/api/123/456', '{}')]
    patches = self.rietveld.get_patch(123, 456)
    self.assertTrue(isinstance(patches, patch.PatchSet))
    self.assertEquals([], patches.patches)

  def _check_patch(self,
      p,
      filename,
      diff,
      source_filename=None,
      is_binary=False,
      is_delete=False,
      is_git_diff=False,
      is_new=False,
      patchlevel=0,
      svn_properties=None):
    svn_properties = svn_properties or []
    self.assertEquals(p.filename, filename)
    self.assertEquals(p.source_filename, source_filename)
    self.assertEquals(p.is_binary, is_binary)
    self.assertEquals(p.is_delete, is_delete)
    if hasattr(p, 'is_git_diff'):
      self.assertEquals(p.is_git_diff, is_git_diff)
    self.assertEquals(p.is_new, is_new)
    if hasattr(p, 'patchlevel'):
      self.assertEquals(p.patchlevel, patchlevel)
    if diff:
      self.assertEquals(p.get(True), diff)
    if hasattr(p, 'svn_properties'):
      self.assertEquals(p.svn_properties, svn_properties)

  def test_get_patch_no_status(self):
    self.requests = [
        ( '/api/123/456',
          _api(
            {
              'tools/clang_check/README.chromium': {
                'status': None,
                'id': 789,
              }})),
        ('/download/issue123_456_789.diff', RAW.DELETE),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(
        patches.patches[0],
        'tools/clang_check/README.chromium',
        RAW.DELETE,
        is_delete=True)

  def test_get_patch_2_files(self):
    self.requests = [
        ('/api/123/456',
          _api({'foo': _file('A'), 'file_a': _file('M', chunk_id=790)})),
        ('/download/issue123_456_789.diff', RAW.NEW),
        ('/download/issue123_456_790.diff', RAW.NEW_NOT_NULL),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(2, len(patches.patches))
    self._check_patch(
        patches.patches[0], 'file_a', RAW.NEW_NOT_NULL, is_new=True)
    self._check_patch(patches.patches[1], 'foo', RAW.NEW, is_new=True)

  def test_get_patch_add(self):
    self.requests = [
        ('/api/123/456', _api({'foo': _file('A')})),
        ('/download/issue123_456_789.diff', RAW.NEW),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(patches.patches[0], 'foo', RAW.NEW, is_new=True)

  def test_invalid_status(self):
    self.requests = [
        ('/api/123/456', _api({'file_a': _file('B')})),
    ]
    try:
      self.rietveld.get_patch(123, 456)
      self.fail()
    except patch.UnsupportedPatchFormat, e:
      self.assertEquals('file_a', e.filename)

  def test_add_plus_merge(self):
    # svn:mergeinfo is dropped.
    properties = (
        '\nAdded: svn:mergeinfo\n'
        '   Merged /branches/funky/file_b:r69-2775\n')
    self.requests = [
        ('/api/123/456',
          _api({'pp': _file('A+', property_changes=properties)})),
        ('/download/issue123_456_789.diff', GIT.COPY),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(
        patches.patches[0],
        'pp',
        GIT.COPY,
        is_git_diff=True,
        is_new=True,
        patchlevel=1,
        source_filename='PRESUBMIT.py')

  def test_add_plus_eol_style(self):
    properties = '\nAdded: svn:eol-style\n   + LF\n'
    self.requests = [
        ('/api/123/456',
          _api({'pp': _file('A+', property_changes=properties)})),
        ('/download/issue123_456_789.diff', GIT.COPY),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(
        patches.patches[0],
        'pp',
        GIT.COPY,
        is_git_diff=True,
        is_new=True,
        patchlevel=1,
        source_filename='PRESUBMIT.py',
        svn_properties=[('svn:eol-style', 'LF')])

  def test_add_empty(self):
    self.requests = [
        ('/api/123/456', _api({'__init__.py': _file('A    ', num_chunks=0)})),
        ('/download/issue123_456_789.diff', RAW.CRAP_ONLY),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(
        patches.patches[0],
        '__init__.py',
        RAW.CRAP_ONLY,
        is_new=True)

  def test_delete(self):
    name = 'tools/clang_check/README.chromium'
    self.requests = [
        ('/api/123/456', _api({name: _file('D')})),
        ('/download/issue123_456_789.diff', RAW.DELETE),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(patches.patches[0], name, RAW.DELETE, is_delete=True)

  def test_delete_empty(self):
    name = 'tests/__init__.py'
    self.requests = [
        ('/api/123/456', _api({name: _file('D')})),
        ('/download/issue123_456_789.diff', GIT.DELETE_EMPTY),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(
        patches.patches[0],
        name,
        GIT.DELETE_EMPTY,
        is_delete=True,
        is_git_diff=True,
        patchlevel=1)

  def test_m_plus(self):
    properties = '\nAdded: svn:eol-style\n   + LF\n'
    self.requests = [
        ('/api/123/456',
          _api({'chrome/file.cc': _file('M+', property_changes=properties)})),
        ('/download/issue123_456_789.diff', RAW.PATCH),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(
        patches.patches[0],
        'chrome/file.cc',
        RAW.PATCH,
        svn_properties=[('svn:eol-style', 'LF')])

  def test_m_plus_unknown_prop(self):
    properties = '\nAdded: svn:foobar\n   + stuff\n'
    self.requests = [
        ('/api/123/456',
          _api({'file_a': _file('M+', property_changes=properties)})),
    ]
    try:
      self.rietveld.get_patch(123, 456)
      self.fail()
    except patch.UnsupportedPatchFormat, e:
      self.assertEquals('file_a', e.filename)

  def test_get_patch_moved(self):
    self.requests = [
        ('/api/123/456', _api({'file_b': _file('A+')})),
        ('/download/issue123_456_789.diff', RAW.MINIMAL_RENAME),
    ]
    patches = self.rietveld.get_patch(123, 456)
    self.assertEquals(1, len(patches.patches))
    self._check_patch(
        patches.patches[0],
        'file_b',
        RAW.MINIMAL_RENAME,
        source_filename='file_a',
        is_new=True)

  def test_svn_properties(self):
    # Line too long (N/80)
    # pylint: disable=C0301

    # To test one of these, run something like
    # import json, pprint, urllib
    # url = 'http://codereview.chromium.org/api/202046/1'
    # pprint.pprint(json.load(urllib.urlopen(url))['files'])

    # svn:mergeinfo across branches:
    # http://codereview.chromium.org/202046/diff/1/third_party/libxml/xmlcatalog_dummy.cc
    self.assertEquals(
        [('svn:eol-style', 'LF')],
        rietveld.Rietveld.parse_svn_properties(
          u'\nAdded: svn:eol-style\n   + LF\n', 'foo'))

    # svn:eol-style property that is lost in the diff
    # http://codereview.chromium.org/202046/diff/1/third_party/libxml/xmllint_dummy.cc
    self.assertEquals(
        [],
        rietveld.Rietveld.parse_svn_properties(
          u'\nAdded: svn:mergeinfo\n'
          '   Merged /branches/chrome_webkit_merge_branch/third_party/'
          'libxml/xmldummy_mac.cc:r69-2775\n',
          'foo'))

    self.assertEquals(
        [],
        rietveld.Rietveld.parse_svn_properties(u'', 'foo'))


    # http://codereview.chromium.org/api/7834045/15001
    self.assertEquals(
        [('svn:executable', '*'), ('svn:eol-style', 'LF')],
        rietveld.Rietveld.parse_svn_properties(
          '\n'
          'Added: svn:executable\n'
          '   + *\n'
          'Added: svn:eol-style\n'
          '   + LF\n',
          'foo'))

    # http://codereview.chromium.org/api/9139006/7001
    self.assertEquals(
        [('svn:mime-type', 'image/png')],
        rietveld.Rietveld.parse_svn_properties(
          '\n'
          'Added: svn:mime-type\n'
          '   + image/png\n',
          'foo'))

  def test_bad_svn_properties(self):
    try:
      rietveld.Rietveld.parse_svn_properties(u'\n', 'foo')
      self.fail()
    except rietveld.patch.UnsupportedPatchFormat, e:
      self.assertEquals('foo', e.filename)
    # TODO(maruel): Change with no diff, only svn property change:
    # http://codereview.chromium.org/6462019/

  def test_search_all_empty(self):
    url = (
        '/search?format=json'
        '&base=base'
        '&created_after=2010-01-02'
        '&created_before=2010-01-01'
        '&modified_after=2010-02-02'
        '&modified_before=2010-02-01'
        '&owner=owner%40example.com'
        '&reviewer=reviewer%40example.com'
        '&closed=2'
        '&commit=2'
        '&private=2'
        '&keys_only=True'
        '&with_messages=True'
        '&limit=23')
    self.requests = [
        (url, '{}'),
    ]
    results = list(self.rietveld.search(
      'owner@example.com',
      'reviewer@example.com',
      'base',
      True,
      True,
      True,
      '2010-01-01',
      '2010-01-02',
      '2010-02-01',
      '2010-02-02',
      23,
      True,
      True,
      ))
    self.assertEquals([], results)

  def test_results_cursor(self):
    # Verify cursor iteration is transparent.
    self.requests = [
        ('/search?format=json&base=base',
          rietveld.json.dumps({
            'cursor': 'MY_CURSOR',
            'results': [{'foo': 'bar'}, {'foo': 'baz'}],
            })),
        ('/search?format=json&base=base&cursor=MY_CURSOR',
          rietveld.json.dumps({
            'cursor': 'NEXT',
            'results': [{'foo': 'prout'}],
            })),
        ('/search?format=json&base=base&cursor=NEXT',
          rietveld.json.dumps({
            'cursor': 'VOID',
            'results': [],
            })),
    ]
    expected = [
        {'foo': 'bar'},
        {'foo': 'baz'},
        {'foo': 'prout'},
    ]
    for i in self.rietveld.search(base='base'):
      self.assertEquals(expected.pop(0), i)
    self.assertEquals([], expected)


if __name__ == '__main__':
  logging.basicConfig(level=[
    logging.ERROR, logging.INFO, logging.DEBUG][min(2, sys.argv.count('-v'))])
  unittest.main()
