require 'formula'

class V8cgi < Formula
  homepage 'http://code.google.com/p/v8cgi/'
  url 'http://v8cgi.googlecode.com/files/v8cgi-0.9.2-src.tar.gz'
  sha1 '790aa7d177cccc94e2cb3ba4ca06213765094f01'

  head 'http://v8cgi.googlecode.com/svn/trunk/'

  depends_on 'scons' => :build
  depends_on 'v8'
  depends_on 'libmemcached'
  depends_on 'xerces-c' if ARGV.include? '--with-dom'
  depends_on 'gd' if ARGV.include? '--with-gd'
  depends_on 'sqlite' if ARGV.include? '--with-sqlite'

  def options
    [
      ["--with-dom", "Enable DOM."],
      ["--with-gd", "Enable GD."],
      ["--with-sqlite", "Enable SQLite."]
    ]
  end

  def install
    arch = Hardware.is_64_bit? ? 'x64' : 'ia32'

    v8_prefix = Formula.factory('v8').prefix

    args = ["config_file=#{etc}/v8cgi.conf", "v8_path=#{v8_prefix}"]
    args << ((ARGV.include? '--with-dom') ? 'dom=1' : 'dom=0')
    args << ((ARGV.include? '--with-gd') ? 'gd=1' : 'gd=0')
    args << ((ARGV.include? '--with-sqlite') ? 'sqlite=1' : 'sqlite=0')

    cd 'v8cgi' do
      inreplace 'SConstruct', '../v8', v8_prefix

      system "scons",
             "-j #{ENV.make_jobs}",
             "arch=#{arch}",
             "library=shared",
             "socket=1",
             "process=1",
             "cgi=1",
             "mysql=0",
             "gl=0",
             "module=0",
             *args

      bin.install 'v8cgi'
      lib.install 'lib' => 'v8cgi'
      etc.install 'v8cgi.conf.darwin' => 'v8cgi.conf'
    end
  end
end
