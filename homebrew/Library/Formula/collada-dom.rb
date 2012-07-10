require 'formula'

class ColladaDom < Formula
  homepage 'http://www.collada.org/mediawiki/index.php/Portal:COLLADA_DOM'
  url 'http://downloads.sourceforge.net/project/collada-dom/Collada%20DOM/Collada%20DOM%202.3/collada_dom-2.3.1-src.tgz'
  md5 'a74d19c1187806a713cec90c2f0f692c'

  depends_on 'cmake' => :build
  depends_on 'pcre'
  depends_on 'boost'

  # Fix build of minizip: quoting arguments to cmake's add_definitions doesn't work the way they thought it did.
  def patches
    return DATA
  end

  def install
    system "cmake", ".", *std_cmake_args
    system "make install"
  end
end

__END__
diff --git a/CMakeLists.txt b/CMakeLists.txt
index 72b6deb..0c7f7ce 100644
--- a/CMakeLists.txt
+++ b/CMakeLists.txt
@@ -100,7 +100,7 @@ endif()

 if( APPLE OR ${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
   # apple doesn't have 64bit versions of file opening functions, so add them
-  add_definitions("-Dfopen64=fopen -Dfseeko64=fseeko -Dfseek64=fseek -Dftell64=ftell -Dftello64=ftello")
+  add_definitions(-Dfopen64=fopen -Dfseeko64=fseeko -Dfseek64=fseek -Dftell64=ftell -Dftello64=ftello)
 endif()

 set(COLLADA_DOM_INCLUDE_INSTALL_DIR "include/collada-dom")
