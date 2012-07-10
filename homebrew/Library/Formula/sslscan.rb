require 'formula'

class Sslscan < Formula
  homepage 'https://www.titania-security.com/labs/sslscan'
  url 'http://sourceforge.net/projects/sslscan/files/sslscan/sslscan%201.8.0/sslscan-1.8.0.tgz'
  md5 '7f5fa87019024366691c6b27cb3a81e7'

  # Remove hardcoded gcc in Makefile
  def patches
    DATA
  end

  def install
    system "make"
    bin.install "sslscan"
    man1.install "sslscan.1"
  end

  def test
    system "#{bin}/sslscan"
  end
end

__END__
diff --git a/Makefile b/Makefile
index a3e1654..b1fbda8 100644
--- a/Makefile
+++ b/Makefile
@@ -3,7 +3,7 @@ BINPATH = /usr/bin/
 MANPATH = /usr/share/man/
 
 all:
-	gcc -lssl -o sslscan $(SRCS) $(LDFLAGS) $(CFLAGS)
+	$(CC) -lssl -lcrypto -o sslscan $(SRCS) $(LDFLAGS) $(CFLAGS)
 
 install:
 	cp sslscan $(BINPATH)

