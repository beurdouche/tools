require 'formula'

class Spin < Formula
  homepage 'http://spinroot.com/spin/whatispin.html'
  url 'http://spinroot.com/spin/Src/spin610.tar.gz'
  version '6.1.0'
  md5 '89c0d322c3a5aded1fda9b0d30327d19'

  fails_with :llvm do
    build 2334
  end

  # replace -DPC with -DMAC in makefile CFLAGS
  def patches
    DATA
  end

  def install
    ENV.deparallelize

    cd("Src#{version}") do
      system "make"
      bin.install "spin"
    end

    man1.install "Man/spin.1"
  end
end

# manual patching is required by the spin install process
__END__
diff --git a/Src6.1.0/makefile b/Src6.1.0/makefile
index 9a9735d..82b5c15 100644
--- a/Src6.1.0/makefile
+++ b/Src6.1.0/makefile
@@ -14,11 +14,11 @@
 # see also ./make_pc for a simpler script, not requiring make
 
 CC=gcc
-CFLAGS=-O2 -ansi -DNXT -D_POSIX_SOURCE -Wno-format-security	# on some systems add: -I/usr/include
+#CFLAGS=-O2 -ansi -DNXT -D_POSIX_SOURCE -Wno-format-security	# on some systems add: -I/usr/include
 
 # CC=cc -m32 	# for 32bit compilation on a 64bit system (not recommended)
 # for a more picky compilation use gcc-4 and:
-# CFLAGS=-std=c99 -Wstrict-prototypes -pedantic -fno-strength-reduce -fno-builtin -W -Wshadow -Wpointer-arith -Wcast-qual -Winline -Wall -g -DNXT -DPC
+CFLAGS=-std=c99 -Wstrict-prototypes -pedantic -fno-strength-reduce -fno-builtin -W -Wshadow -Wpointer-arith -Wcast-qual -Winline -Wall -g -DNXT -DMAC
 
 # on OS2:		spin -Picc -E/Pd+ -E/Q+
 # for Visual C++:	spin -PCL  -E/E
