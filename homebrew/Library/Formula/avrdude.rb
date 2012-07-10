require 'formula'

class Avrdude < Formula
  url 'http://download.savannah.gnu.org/releases/avrdude/avrdude-5.11.1.tar.gz'
  homepage 'http://savannah.nongnu.org/projects/avrdude/'
  md5 '3a43e288cb32916703b6945e3f260df9'

  depends_on 'libusb-compat' if ARGV.include? '--with-usb'

  def options
    [['--with-usb', 'Compile AVRDUDE with USB support.']]
  end

  def install
    system "./configure", "--disable-dependency-tracking", "--prefix=#{prefix}"
    system "make"
    system "make install"
  end
end
