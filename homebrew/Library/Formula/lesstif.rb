require 'formula'

class Lesstif < Formula
  homepage 'http://lesstif.sourceforge.net'
  url 'http://sourceforge.net/projects/lesstif/files/lesstif/0.95.2/lesstif-0.95.2.tar.bz2'
  md5 '754187dbac09fcf5d18296437e72a32f'

  depends_on :x11

  def install
    # LessTif does naughty, naughty, things by assuming we want autoconf macros
    # to live in wherever `aclocal --print-ac-dir` says they should.

    inreplace ['configure'], "`aclocal --print-ac-dir`", "#{share}/aclocal"

    # Shame on you LessTif! *wags finger*

    system "./configure", "--prefix=#{prefix}",
                          "--disable-debug",
                          "--enable-production",
                          "--disable-dependency-tracking",
                          "--enable-shared",
                          "--enable-static"

    system "make"

    # LessTif won't install in parallel 'cause several parts of the Makefile will
    # try to make the same directory and `mkdir` will fail.
    ENV.deparallelize
    system "make install"
  end
end
