import sys
import os
import subprocess
import shutil

print("=" * 50)
print("🔍 فحص جاهزية بيئة البيانات الضخمة (Environment Diagnostics)")
print("=" * 50)

# 1. فحص بايثون
print(f"🐍 Python Executable : {sys.executable}")
print(f"📌 Python Version    : {sys.version.split()[0]}")

# 2. فحص Java / JDK
java_path = shutil.which("java")
print(f"\n☕ Java Executable   : {java_path if java_path else '❌ NOT FOUND'}")
java_home = os.environ.get("JAVA_HOME", "❌ NOT SET")
print(f"📌 JAVA_HOME         : {java_home}")
if java_path:
    try:
        res = subprocess.run(["java", "-version"], capture_output=True, text=True)
        v_line = res.stderr.splitlines()[0] if res.stderr else "Unknown"
        print(f"ℹ️  Java Version Info: {v_line}")
    except Exception as e:
        print(f"⚠️  Could not retrieve Java version: {e}")

# 3. فحص Hadoop & Winutils (خاص بويندوز)
hadoop_home = os.environ.get("HADOOP_HOME", "C:\\hadoop")
winutils_file = os.path.join(hadoop_home, "bin", "winutils.exe")
hadoop_dll = os.path.join(hadoop_home, "bin", "hadoop.dll")
print(f"\n🐘 HADOOP_HOME       : {hadoop_home}")
print(f"📦 winutils.exe      : {'✅ FOUND' if os.path.exists(winutils_file) else '❌ MISSING'}")
print(f"📦 hadoop.dll        : {'✅ FOUND' if os.path.exists(hadoop_dll) else '❌ MISSING'}")

# 4. فحص الحزم والمكتبات المثبتة (Pip / Packages)
print("\n📦 فحص المكتبات الأساسية:")
packages = ["pyspark", "pymongo", "pytest"]
for pkg in packages:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "Installed")
        print(f"  ✅ {pkg:<10} : {ver}")
    except ImportError:
        print(f"  ❌ {pkg:<10} : NOT INSTALLED")

# 5. اختبار خفيف لاتصال MongoDB
print("\n🍃 فحص اتصال MongoDB محلياً:")
try:
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    client.server_info()
    print("  ✅ MongoDB is RUNNING & Accessible.")
    client.close()
except Exception as e:
    print(f"  ❌ MongoDB Connection FAILED: {e}")

print("=" * 50)