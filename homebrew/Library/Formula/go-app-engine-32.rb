require 'formula'

class GoAppEngine32 < Formula
  url 'http://googleappengine.googlecode.com/files/go_appengine_sdk_darwin_386-1.6.6.zip'
  homepage 'http://code.google.com/appengine/docs/go/overview.html'
  sha1 'cd234195261bf0731018e17762fe75fc2c088dba'

  def install
    cd '..'
    share.install 'google_appengine' => name
    bin.mkpath
    %w[appcfg.py bulkload_client.py bulkloader.py dev_appserver.py remote_api_shell.py].each do |fn|
      ln_s share+name+fn, bin
    end
  end
end
