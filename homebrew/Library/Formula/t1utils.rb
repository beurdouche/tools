require 'formula'

class T1utils < Formula
  url 'http://www.lcdf.org/type/t1utils-1.37.tar.gz'
  homepage 'http://www.lcdf.org/type/'
  sha256 '42bdce77aaf12b33ca6d193e01a2d2c0012f755435a6d25921f94733ee61cec3'

  def install
    system "./configure", "--prefix=#{prefix}", "--disable-dependency-tracking"
    system "make install"
  end

  def test
    system "#{bin}/t1mac --version | head -1"
  end
end
