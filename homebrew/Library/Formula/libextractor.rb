require 'formula'

class Libextractor < Formula
  homepage 'http://www.gnu.org/software/libextractor/'
  url 'http://ftpmirror.gnu.org/libextractor/libextractor-0.6.2.tar.gz'
  mirror 'http://ftp.gnu.org/gnu/libextractor/libextractor-0.6.2.tar.gz'
  md5 '4b2af1167061430d58a101d5dfc6b4c7'

  depends_on 'libtool' => :build unless MacOS.lion?

  def install
    ENV.deparallelize
    system "./configure", "--disable-debug",
                          "--disable-dependency-tracking",
                          "--prefix=#{prefix}"
    system "make install"
  end

  def test
    system "#{bin}/extract", "-v"
  end
end
