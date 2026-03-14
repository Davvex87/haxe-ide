package;

import haxe.io.Path;
import sys.io.File;
import sys.io.Process;
import sys.FileSystem;

using StringTools;

class Run
{
	static function main()
	{
		if (Sys.systemName() == "BSD" || Sys.systemName() == "Mac")
		{
			Sys.stderr().writeString("Haxe-IDE is not supported on FreeBSD and MacOS systems yet.\n");
			// TODO: Or maybe it is, idk I can't test it, if anyone reading this has any of these systems and can test it, please do and lmk, thanks <3
			Sys.exit(1);
			return;
		}

		var args = Sys.args();
		args.pop();
		if (args[0] == "setup")
		{
			final linkPath = getLibLinkPath();
			var libDir = FileSystem.absolutePath(getLibraryDir());
			if (isWin)
			{
				var f = File.write(linkPath, false);
				f.writeString('@"${Path.join([libDir, "haxe-ide.exe"])}" %*');
				f.close();
			}
			else
			{
				if (libDir == null)
				{
					Sys.stderr().writeString("What?\nRun \x1b[1;35m'haxelib --global install haxe-ide'\x1b[0m and try again.\n");
					Sys.exit(1);
					return;
				}

				final scriptPath = Path.join([libDir, "haxe-ide"]);

				final linkStr = FileSystem.absolutePath(linkPath);
				final scriptStr = FileSystem.absolutePath(scriptPath);
				Sys.command("chmod", ["+x", scriptStr]);
				if (FileSystem.exists(linkPath))
					Sys.command("sudo", ["rm", linkStr]);
				Sys.command("sudo", ["ln", "-s", scriptStr, linkStr]);
			}

			Sys.println("Haxe-IDE setup complete! You can now run \x1b[1;34m'haxe-ide'\x1b[0m from the command line to start the IDE.");

			return;
		}

		Sys.stderr().writeString("Run \x1b[1;34m'haxe-ide'\x1b[0m from the command line to open the editor.\nCommand not found? Run \x1b[1;35m'haxelib --global run haxe-ide setup'\x1b[0m and try again.\n");
		Sys.exit(2);
	}

	public static var isWin(get, never):Bool;
	static function get_isWin():Bool
		return Sys.systemName() == "Windows";

	public static function getLibLinkPath():String
	{
		if (isWin)
			return Path.join([Sys.getEnv("HAXEPATH"), "haxe-ide.bat"]);

		return "/usr/local/bin/haxe-ide";
	}

	public static function getLibraryDir():Null<String>
	{
		try
		{
			var process = new Process('haxelib --global libpath haxe-ide');
			if (process.exitCode() != 0)
				return null;

			var output = process.stdout.readAll().toString();
			process.close();

			return output.replace("\n", "").replace("\r", "");
		}
		catch (e:Dynamic) {}
		return null;
	}
}