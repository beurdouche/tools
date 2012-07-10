require 'formula'

class Neon < Formula
  url 'http://www.webdav.org/neon/neon-0.29.6.tar.gz'
  md5 '591e0c82e6979e7e615211b386b8f6bc'
  homepage 'http://www.webdav.org/neon/'

  depends_on 'pkg-config' => :build

  keg_only :provided_by_osx,
            "Compiling newer versions of Subversion on 10.6 require this newer neon."

  def options
    [['--universal', 'Builds a universal binary.']]
  end

  def install
    ENV.universal_binary if ARGV.build_universal?

    system "./configure", "--prefix=#{prefix}",
                          "--disable-debug",
                          "--enable-shared",
                          "--disable-static",
                          "--with-ssl"
    system "make install"
  end
end
