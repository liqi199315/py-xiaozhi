# 修复 Android Studio 运行配置错误

## 错误信息
```
Error running 'app'
Activity class(com,xiaozhi.app/com.eshowcaseai.app.MainActivity} does not exist
```

## 问题原因
Android Studio 的运行配置和缓存中还保留着旧包名 `com.xiaozhi.app`

## 解决方案（按顺序执行）

### 方案一：重置运行配置（推荐，最快）

1. **删除当前运行配置**
   - 点击顶部工具栏的运行配置下拉框（显示 "app" 的地方）
   - 选择 "Edit Configurations..."
   - 在左侧找到 "app" 配置
   - 点击顶部的 `-` 按钮删除
   - 点击 "Apply" 和 "OK"

2. **重新同步项目**
   - 点击 `File` -> `Sync Project with Gradle Files`
   - 等待同步完成

3. **Android Studio 会自动创建新的运行配置**
   - 此时会使用正确的包名 `com.eshowcaseai.app`

### 方案二：清理所有缓存（彻底）

```bash
# 1. 在 Android Studio 中执行
# File -> Invalidate Caches... -> 勾选以下选项
# - Clear file system cache and Local History
# - Clear downloaded shared indexes
# - Clear VCS Log caches and indexes
# 点击 "Invalidate and Restart"

# 2. 或者手动删除缓存目录（需要关闭 Android Studio）
cd c:\Users\Administrator\Desktop\project-active\py-xiaozhi\Android

# 删除 Gradle 缓存
rm -rf .gradle
rm -rf build
rm -rf app/build

# 删除 Android Studio 缓存（可选，彻底清理）
rm -rf .idea
```

### 方案三：命令行安装（绕过 Android Studio）

```bash
# 1. 清理构建
cd c:\Users\Administrator\Desktop\project-active\py-xiaozhi\Android
./gradlew clean

# 2. 卸载旧版本
adb uninstall com.xiaozhi.app
adb uninstall com.eshowcaseai.app

# 3. 构建并安装
./gradlew installDebug

# 4. 手动启动应用
adb shell am start -n com.eshowcaseai.app/.MainActivity
```

## 详细步骤说明

### 步骤 1: 删除运行配置

<details>
<summary>点击查看详细截图说明</summary>

1. 在 Android Studio 顶部工具栏找到这个位置：
   ```
   [app] ▼  [设备选择器]  ▶️ (运行按钮)
   ```

2. 点击 `[app] ▼` 下拉箭头

3. 选择 "Edit Configurations..."

4. 在弹出窗口左侧看到：
   ```
   Android App
   └── app  ← 选中这个
   ```

5. 点击顶部的 `-` (减号) 按钮删除

6. 点击 "OK"

</details>

### 步骤 2: 同步项目

```
File -> Sync Project with Gradle Files
```
等待进度条完成（右下角）

### 步骤 3: 重新运行

- 点击绿色运行按钮 ▶️
- Android Studio 会自动创建新的运行配置
- 使用正确的包名 `com.eshowcaseai.app`

## 验证修复成功

### 检查运行配置
1. 点击 "Edit Configurations..."
2. 查看 "Launch" 选项
3. 确认显示：
   ```
   Launch: Default Activity
   ```

### 检查设备上的进程
```bash
# 运行应用后执行
adb shell ps | grep eshowcaseai

# 应该看到：
# u0_a123  12345  ... com.eshowcaseai.app
```

## 如果还是不行

### 最后的绝招：完全重置

```bash
# 1. 关闭 Android Studio

# 2. 删除所有缓存
cd c:\Users\Administrator\Desktop\project-active\py-xiaozhi\Android
rm -rf .gradle
rm -rf .idea
rm -rf build
rm -rf app/build
rm -rf app/.cxx

# 3. 卸载设备上的所有版本
adb uninstall com.xiaozhi.app
adb uninstall com.eshowcaseai.app

# 4. 重新打开项目
# 在 Android Studio 中: File -> Open -> 选择 Android 目录

# 5. 等待 Gradle 同步完成

# 6. 运行应用
```

## 常见问题

### Q: 为什么错误信息显示 "com,xiaozhi.app" (逗号)?
**A:** 这是 Android Studio 内部存储的旧配置格式问题，删除运行配置即可解决。

### Q: 删除运行配置后找不到 app 配置了？
**A:** 正常现象，点击 "Sync Project with Gradle Files" 后会自动创建新的。

### Q: Sync 后还是没有运行配置？
**A:** 手动创建：
1. Edit Configurations -> `+` -> Android App
2. Name: `app`
3. Module: `xiaozhi-android.app.main`
4. Launch: Default Activity
5. Apply -> OK

## 预防措施

以后修改包名时，记得同时执行：
1. `File -> Invalidate Caches and Restart`
2. 删除运行配置并重新创建
3. `./gradlew clean`
