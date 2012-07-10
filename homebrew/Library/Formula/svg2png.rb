require 'formula'

class Svg2png < Formula
  url 'http://cairographics.org/snapshots/svg2png-0.1.3.tar.gz'
  homepage 'http://cairographics.org/'
  md5 'ba266c00486ffd93b8a46d59028aaef9'

  depends_on 'pkg-config' => :build
  depends_on 'libsvg-cairo'

  def install
    system "./configure", "--disable-debug", "--disable-dependency-tracking",
                          "--prefix=#{prefix}",
                          "--mandir=#{man}"
    system "make install"
  end
end
