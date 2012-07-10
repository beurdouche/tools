# This software is in the public domain, furnished "as is", without technical
# support, and with no warranty, express or implied, as to its usefulness for
# any purpose.

# Require this file to build a testing environment.

ABS__FILE__=File.expand_path(__FILE__)

$:.push(File.expand_path(__FILE__+'/../..'))
require 'extend/pathname'
require 'exceptions'
require 'utils'

# these are defined in global.rb, but we don't want to break our actual
# homebrew tree, and we do want to test everything :)
HOMEBREW_PREFIX=Pathname.new '/private/tmp/testbrew/prefix'
HOMEBREW_REPOSITORY=HOMEBREW_PREFIX
HOMEBREW_CACHE=HOMEBREW_PREFIX.parent+"cache"
HOMEBREW_CACHE_FORMULA=HOMEBREW_PREFIX.parent+"formula_cache"
HOMEBREW_CELLAR=HOMEBREW_PREFIX.parent+"cellar"
HOMEBREW_USER_AGENT="Homebrew"
HOMEBREW_WWW='http://example.com'
HOMEBREW_CURL_ARGS = '-fsLA'
MACOS_VERSION=10.6

(HOMEBREW_PREFIX+'Library/Formula').mkpath
Dir.chdir HOMEBREW_PREFIX
at_exit { HOMEBREW_PREFIX.parent.rmtree }

# Test fixtures and files can be found relative to this path
TEST_FOLDER = Pathname.new(ABS__FILE__).parent.realpath

require 'fileutils'
module Homebrew extend self
  include FileUtils
end

def shutup
  if ARGV.verbose?
    yield
  else
    begin
      tmperr = $stderr.clone
      tmpout = $stdout.clone
      $stderr.reopen '/dev/null', 'w'
      $stdout.reopen '/dev/null', 'w'
      yield
    ensure
      $stderr.reopen tmperr
      $stdout.reopen tmpout
    end
  end
end

unless ARGV.include? "--no-compat" or ENV['HOMEBREW_NO_COMPAT']
  $:.unshift(File.expand_path("#{ABS__FILE__}/../../compat"))
  require 'compatibility'
end

require 'test/unit' # must be after at_exit

require 'extend/ARGV' # needs to be after test/unit to avoid conflict with OptionsParser
ARGV.extend(HomebrewArgvExtension)

require 'extend/ENV'
ENV.extend(HomebrewEnvExtension)
