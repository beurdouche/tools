require 'formula'

class Tinysvm < Formula
  homepage 'http://chasen.org/~taku/software/TinySVM/'
  url 'http://chasen.org/~taku/software/TinySVM/src/TinySVM-0.09.tar.gz'
  md5 '22d80bdd94c3c8373062761de0d27fde'

  # Use correct compilation flag
  def patches
    { :p0 => [
      "https://trac.macports.org/export/94156/trunk/dports/math/TinySVM/files/patch-configure.diff"
    ]}
  end

  def install
    # Needed to select proper getopt, per MacPorts
    ENV.append_to_cflags '-D__GNU_LIBRARY__'

    system "./configure", "--disable-debug",
                          "--disable-dependency-tracking",
                          "--prefix=#{prefix}",
                          "--mandir=#{man}",
                          "--disable-shared"
    system "make install"
  end

  def test
    system "#{bin}/svm_learn --help"
    system "#{bin}/svm_classify --help"
    system "#{bin}/svm_model --help"
  end
end
