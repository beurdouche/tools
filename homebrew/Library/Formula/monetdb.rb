require 'formula'

class Monetdb < Formula
  homepage 'http://www.monetdb.org/'
  url 'http://dev.monetdb.org/downloads/sources/Apr2012-SP1/MonetDB-11.9.5.tar.bz2'
  sha1 '28b0b86a417581414e506664ab03a1bd6b9d94c7'

  head 'http://dev.monetdb.org/hg/MonetDB', :using => :hg

  depends_on 'pcre'
  depends_on 'readline' # Compilation fails with libedit.

  def install
    system "./bootstrap" if ARGV.build_head?

    system "./configure", "--prefix=#{prefix}",
                          "--enable-debug=no",
                          "--enable-assert=no",
                          "--enable-optimize=yes",
                          "--enable-testing=no",
                          "--without-rubygem"
    system "make install"
  end
end
