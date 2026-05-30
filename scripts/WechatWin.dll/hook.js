function readStdString(s) {
    var flag = s.add(23).readU8()
    if (flag == 0x80) {
        // 从堆中读取
        var size = s.add(8).readUInt()
        return s.readPointer().readUtf8String(size)
    } else {
        // 从栈中读取
        return s.readUtf8String(flag)
    }
}
function writeStdString(s, content) {
    var flag = s.add(23).readU8()
    if (flag == 0x80) {
        // 从堆中写入
        var orisize = s.add(8).readUInt()
        if (content.length > orisize) {
            throw "must below orisize!"
        }
        s.readPointer().writeUtf8String(content)
        s.add(8).writeUInt(content.length)
    } else {
        // 从栈中写入
        if (content.length > 22) {
            throw "max 23 for stack str"
        }
        s.writeUtf8String(content)
        s.add(23).writeU8(content.length)
    }
}



function findExport(moduleName, exportName) {
    if (typeof Module.getGlobalExportByName === "function") {
        return Module.getGlobalExportByName(exportName);
    }
    if (typeof Module.findExportByName === "function") {
        return Module.findExportByName(moduleName, exportName);
    }
    throw new Error("No compatible Frida export lookup API is available");
}

function enableXWebInspect(cmdline) {
    if (!cmdline) {
        return "";
    }
    var updated = cmdline.replace(/--log-level=2/g, "--log-level=0 --xweb-enable-inspect=1");
    if (updated.indexOf("--type=wxpublic") !== -1 || isTopLevelWeChatAppEx(updated)) {
        updated = appendH5DevToolsFlags(updated);
    }
    return updated;
}

function isTopLevelWeChatAppEx(cmdline) {
    return cmdline.indexOf("WeChatAppEx.exe") !== -1
        && cmdline.indexOf("--helper-handle-value") !== -1
        && cmdline.indexOf("--type=") === -1;
}

function appendH5DevToolsFlags(cmdline) {
    var updated = cmdline;
    if (updated.indexOf("--xweb-enable-inspect") === -1) {
        updated += " --xweb-enable-inspect=1";
    }
    if (updated.indexOf("--remote-debugging-port=") === -1) {
        updated += " --remote-debugging-port=9222";
    }
    if (updated.indexOf("--remote-debugging-address=") === -1) {
        updated += " --remote-debugging-address=127.0.0.1";
    }
    if (updated.indexOf("--remote-allow-origins=") === -1) {
        updated += " --remote-allow-origins=*";
    }
    return updated;
}

// 创建一个函数，用于拦截CreateProcessW函数
var cpsPtr = findExport("kernel32.dll", "CreateProcessW");
if (cpsPtr === null) {
    throw new Error("CreateProcessW export not found");
}

// 拦截CreateProcessW函数，在函数调用前和调用后分别执行onEnter和onLeave函数
Interceptor.attach(cpsPtr, {
    onEnter: function (args) {
        // 获取CreateProcessW函数的参数
        this.pi = args[9];
        this.exepath = args[0];
        this.cmdline = args[1];
        let aaa = this.cmdline.isNull() ? "" : this.cmdline.readUtf16String();
        // 替换参数中的--log-level=2为--log-level=0 --xweb-enable-inspect=1
        aaa = enableXWebInspect(aaa);
        this.rewrittenCmdline = Memory.allocUtf16String(aaa);
        args[1] = this.rewrittenCmdline;
        this.cmdline = args[1];
    },
    onLeave: function (retval) {
        // send("[+] 可执行路径："+this.exepath.readUtf16String())
       
        // 打印可执行路径
        // send("[+] 可执行路径："+this.exepath.readUtf16String())
        
        // // 打印命令行参数
        send("[+] 命令行参数："+this.cmdline.readUtf16String());
        //--xweb-enable-inspect
        // 打印进程id
    //    send("[+] 进程id: "+this.cmdline.readUtf16String());
    }
}
);
