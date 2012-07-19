require 'formula'

class Io < Formula
  homepage 'http://iolanguage.com/'
  url 'https://github.com/stevedekorte/io/tarball/2011.09.12'
  sha1 '56720fe9b2c746ca817c15e48023b256363b3015'

  head 'https://github.com/stevedekorte/io.git'

  depends_on 'cmake' => :build
  depends_on 'ossp-uuid'
  depends_on 'libevent'
  depends_on 'yajl'
  depends_on 'libffi'
  depends_on 'pcre'

  # Fix recursive inline. See discussion in:
  # https://github.com/stevedekorte/io/issues/135
  def patches
    DATA
  end

  def install
    ENV.j1
    mkdir 'buildroot' do
      system "cmake", "..", *std_cmake_args
      system 'make'
      output = %x[./_build/binaries/io ../libs/iovm/tests/correctness/run.io]
      if $?.exitstatus != 0
        opoo "Test suite not 100% successful:\n#{output}"
      else
        ohai "Test suite ran successfully:\n#{output}"
      end
      system 'make install'
    end
  end
end

__END__
--- a/libs/basekit/source/Common_inline.h	2011-09-12 17:14:12.000000000 -0500
+++ b/libs/basekit/source/Common_inline.h	2011-12-17 00:46:02.000000000 -0600
@@ -52,7 +52,7 @@
 
 #if defined(__APPLE__) 
 
-	#define NS_INLINE static __inline__ __attribute__((always_inline))
+	#define NS_INLINE static inline
 
 	#ifdef IO_IN_C_FILE
 		// in .c 
