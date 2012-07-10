require 'formula'

class ImapUw < Formula
  homepage 'http://www.washington.edu/imap/'
  url 'ftp://ftp.cac.washington.edu/imap/imap-2007f.tar.gz'
  sha1 '7a82ebd5aae57a5dede96ac4923b63f850ff4fa7'

  def patches
    if MacOS.snow_leopard?
      { :p0 =>
        'https://trac.macports.org/export/63088/trunk/dports/mail/imap-uw/files/patch-snowleopard.diff'
      }
    end
  end

  def install
    ENV.j1

    system 'make oxp'

    # email servers:
    sbin.install 'imapd/imapd', 'ipopd/ipop2d', 'ipopd/ipop3d'

    # mail utilities:
    bin.install 'dmail/dmail', 'mailutil/mailutil', 'tmail/tmail'

    # c-client library:
    #   Note: Installing the headers from the root c-client directory is not
    #   possible because they are symlinks and homebrew dutifully copies them
    #   as such. Pulling from within the src dir achieves the desired result.
    doc.install Dir['docs/*']
    lib.install 'c-client/c-client.a' => 'libc-client.a'
    (include + 'imap').install 'c-client/osdep.h', 'c-client/linkage.h'
    (include + 'imap').install Dir['src/c-client/*.h', 'src/osdep/unix/*.h']
  end
end
