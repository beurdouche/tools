require 'formula'

class Xar < Formula
  homepage 'http://code.google.com/p/xar/'
  url 'http://xar.googlecode.com/files/xar-1.5.2.tar.gz'
  md5 '8eabb055d3387b8edc30ecfb08d2e80d'

  # Known issue upstream:
  # http://code.google.com/p/xar/issues/detail?id=51
  def patches
    DATA
  end

  def install
    system "./configure", "--disable-debug", "--disable-dependency-tracking",
                          "--prefix=#{prefix}",
                          "--mandir=#{man}"
    system "make"
    system "make install"
  end
end


__END__
diff -Naur old/lib/archive.c new/lib/archive.c
--- old/lib/archive.c
+++ new/lib/archive.c
@@ -79,6 +79,10 @@
 #define LONG_MIN INT32_MIN
 #endif
 
+#if LIBXML_VERSION < 20618
+#define xmlDictCleanup()        /* function doesn't exist in older API */
+#endif
+
 static int32_t xar_unserialize(xar_t x);
 void xar_serialize(xar_t x, const char *file);
