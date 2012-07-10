require 'formula'

class Pdksh < Formula
  homepage 'http://www.cs.mun.ca/~michael/pdksh/'
  url 'http://www.cs.mun.ca/~michael/pdksh/files/pdksh-5.2.14.tar.gz'
  md5 '871106b3bd937e1afba9f2ef7c43aef3'

  # Use a sort command that works with Leopard and up
  def patches
  { :p0 =>
    "https://trac.macports.org/export/90549/trunk/dports/shells/pdksh/files/patch-siglist.sh.diff"
  }
  end

  def install
    # --mandir does not work for this
    inreplace "Makefile.in",
                "$(prefix)/man/man$(manext)",
                "$(prefix)/share/man/man1"

    system "./configure", "--disable-debug", "--disable-dependency-tracking",
                          "--prefix=#{prefix}"
    system "make"
    system "make install"
  end
end
