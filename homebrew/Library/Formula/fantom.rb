require 'formula'

class Fantom < Formula
  homepage 'http://fantom.org'
  url 'http://fan.googlecode.com/files/fantom-1.0.62.zip'
  md5 '253acd05563b58b41f8381435586e3d6'

  def options
    [['--with-src', 'Also install fantom source'],
     ['--with-examples', 'Also install fantom examples']]
  end

  # Select the OS X JDK path in the config file
  def patches; DATA; end

  def install
    rm_f Dir["bin/*.exe", "lib/dotnet/*"]
    rm_rf "examples" unless ARGV.include? '--with-examples'
    rm_rf "src" unless ARGV.include? '--with-src'

    libexec.install Dir['*']
    system "chmod 0755 #{libexec}/bin/*"
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end
end

__END__
diff --git a/etc/build/config.props b/etc/build/config.props
index c6675f1..b8423fe 100644
--- a/etc/build/config.props
+++ b/etc/build/config.props
@@ -12,8 +12,8 @@ buildVersion=1.0.62
 //devHome=file:/E:/fan/
 
 // Windows setup
-jdkHome=/C:/Program Files/Java/jdk1.6.0_21/
-dotnetHome=/C:/WINDOWS/Microsoft.NET/Framework/v2.0.50727/
+//jdkHome=/C:/Program Files/Java/jdk1.6.0_21/
+//dotnetHome=/C:/WINDOWS/Microsoft.NET/Framework/v2.0.50727/
 
 // Mac setup
-//jdkHome=/System/Library/Frameworks/JavaVM.framework/Versions/CurrentJDK/Home/
\ No newline at end of file
+jdkHome=/System/Library/Frameworks/JavaVM.framework/Versions/CurrentJDK/Home/
