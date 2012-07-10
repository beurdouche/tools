require 'formula'

class Crossroads < Formula
  homepage 'http://www.crossroads.io/'
  url 'http://download.crossroads.io/libxs-1.2.0.tar.gz'
  sha1 'd9633e6df56e3ed0c4f0e86d80ee0ae10c8a966a'

  head 'https://github.com/crossroads-io/libxs.git'

  depends_on :automake
  depends_on :libtool

  def options
    [['--with-pgm', 'Build with PGM extension']]
  end

  fails_with :llvm do
    build 2326
    cause "Compiling with LLVM gives a segfault while linking."
  end

  def install
    system "./autogen.sh" if ARGV.build_head?

    args = ["--disable-dependency-tracking", "--prefix=#{prefix}"]
    args << "--with-pgm" if ARGV.include? '--with-pgm'
    system "./configure", *args

    system "make"
    system "make install"
  end
end
