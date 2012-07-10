require 'formula'

class Dos2unix < Formula
  homepage 'http://waterlan.home.xs4all.nl/dos2unix.html'
  url 'http://waterlan.home.xs4all.nl/dos2unix/dos2unix-6.0.tar.gz'
  sha1 '77ff5b9203f2a0abc4900c00d69e8d5b67d617a5'

  depends_on "gettext" if ARGV.include? "--enable-nls"

  def options
    [["--enable-nls", "Enable NLS support."]]
  end

  def install
    args = ["prefix=#{prefix}"]

    if ARGV.include? "--enable-nls"
      gettext = Formula.factory("gettext")
      args << "CFLAGS_OS=-I#{gettext.include}"
      args << "LDFLAGS_EXTRA=-L#{gettext.lib} -lintl"
    else
      args << "ENABLE_NLS="
    end

    args << "CC=#{ENV.cc}"
    args << "CPP=#{ENV.cc}"
    args << "CFLAGS=#{ENV.cflags}"
    args << "install"

    system "make", *args
  end
end
