require 'formula'

class XercesC < Formula
  url 'http://www.apache.org/dyn/closer.cgi?path=xerces/c/3/sources/xerces-c-3.1.1.tar.gz'
  homepage 'http://xerces.apache.org/xerces-c/'
  md5 '6a8ec45d83c8cfb1584c5a5345cb51ae'

  def install
    system "./configure", "--disable-dependency-tracking", "--prefix=#{prefix}"
    system "make install"
  end
end
