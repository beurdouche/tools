require 'formula'

class Sleepwatcher < Formula
  homepage 'http://www.bernhard-baehr.de/'
  url 'http://www.bernhard-baehr.de/sleepwatcher_2.2.tgz'
  md5 '2a9235c7da4ad4ed9fb3181203849ded'

  def install
    # Adjust Makefile to build native binary only
    inreplace "sources/Makefile" do |s|
      s.gsub! /^(CFLAGS)_PPC.*$/, "\\1 = #{ENV.cflags} -prebind"
      s.gsub! /^(CFLAGS_X86)/, "#\\1"
      s.change_make_var! "BINDIR", "$(PREFIX)/sbin"
      s.change_make_var! "MANDIR", "$(PREFIX)/share/man"
      s.gsub! /^(.*?)CFLAGS_PPC(.*?)[.]ppc/, "\\1CFLAGS\\2"
      s.gsub! /^(.*?CFLAGS_X86.*?[.]x86)/, "#\\1"
      s.gsub! /^(\t(lipo|rm).*?[.](ppc|x86))/, "#\\1"
      s.gsub! "-o root -g wheel", ""
    end

    # Build and install binary
    cd "sources" do
      system "mv", "../sleepwatcher.8", "."
      system "make", "install", "PREFIX=#{prefix}"
    end

    # Write the usage ReadMe
    prefix.install "ReadMe.rtf"

    # Write the sleep/wakeup scripts
    (prefix + 'etc/sleepwatcher').install Dir["config/rc.*"]

    # Write the launchd scripts
    inreplace Dir["config/*.plist"] do |s|
      s.gsub! "/etc", (etc + 'sleepwatcher')
      s.gsub! "/usr/local/sbin", (HOMEBREW_PREFIX + 'sbin')
    end
    prefix.install Dir["config/*.plist"]
  end

  def caveats; <<-EOS.undent
    For SleepWatcher to work, you will need to read the following:

      #{prefix}/ReadMe.rtf

    Ignore information about installing the binary and man page,
    but read information regarding setup of the launchd files which
    are installed here:

      #{Dir[(prefix + '*.plist')].join("\n      ")}

    These are the examples provided by the author.
    EOS
  end
end
