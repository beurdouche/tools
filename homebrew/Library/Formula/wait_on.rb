require 'formula'

class WaitOn < Formula
  homepage 'http://www.freshports.org/sysutils/wait_on/'
  url 'ftp://ftp.ugh.net.au/pub/unix/wait_on/wait_on-1.1.tar.gz'
  sha1 '9e3fb51b6324f5aca7664fb8165f61a52bd5bd61'

  depends_on :bsdmake

  def install
    system "bsdmake"
    bin.install 'wait_on'
    man1.install 'wait_on.1.gz'
  end

  def test
    system "#{bin}/wait_on", "-v"
  end
end
