require 'formula'

class PureDocs < Formula
  url 'http://pure-lang.googlecode.com/files/pure-docs-0.53.tar.gz'
  sha1 'c0ad274d344d982e65b15b63daf3a267c50ab186'
end

class Pure < Formula
  homepage 'http://code.google.com/p/pure-lang/'
  url 'http://pure-lang.googlecode.com/files/pure-0.53.tar.gz'
  sha1 '67f1394c06d885b79fc824283f0f7551a6fb2641'

  depends_on 'llvm'
  depends_on 'gmp'
  depends_on 'readline'
  depends_on 'mpfr'

  def install
    system "./configure", "--disable-debug",
                          "--prefix=#{prefix}",
                          "--enable-release",
                          "--without-elisp"
    system "make"
    system "make check"
    system "make install"

    PureDocs.new.brew { system "make", "prefix=#{prefix}", "install" }
  end
end
