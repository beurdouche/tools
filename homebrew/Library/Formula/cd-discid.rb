require 'formula'

class CdDiscid < Formula
  url 'http://linukz.org/download/cd-discid-1.1.tar.gz'
  homepage 'http://linukz.org/cd-discid.shtml'
  md5 '04cb368e3f1ce17e656ac6691ca0b687'

  def patches
  { :p0 =>
    "https://trac.macports.org/export/70630/trunk/dports/audio/cd-discid/files/patch-cd-discid.c.diff"
  }
  end

  def install
    system "make", "prefix=#{prefix}",
                   "CC=#{ENV.cc}",
                   "CFLAGS=#{ENV.cflags}",
                   "install"
  end
end
