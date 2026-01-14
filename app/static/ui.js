// 通用工具
const Utils = {
    async copy(text) {
        // 如果 text 是相对路径，自动转换为完整 URL
        if (text.startsWith('/')) {
            text = window.location.origin + text;
        }

        try {
            await navigator.clipboard.writeText(text);
            Toast.show('已复制到剪贴板');
            return true;
        } catch (err) {
            // Fallback for older browsers or mobile webview
            try {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed'; // Prevent scrolling
                textarea.style.left = '-9999px';
                textarea.style.top = '0';
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                const successful = document.execCommand('copy');
                document.body.removeChild(textarea);
                if (successful) {
                    Toast.show('已复制到剪贴板');
                    return true;
                }
            } catch (fallbackErr) {
                console.error(fallbackErr);
            }
            
            Toast.show('复制失败，请手动复制', 'error');
            return false;
        }
    },
    
    setLoading(btn, isLoading) {
        if (!btn) return;
        if (isLoading) {
            btn.dataset.originalText = btn.innerHTML;
            btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg> 处理中...`;
            btn.classList.add('loading');
            btn.disabled = true;
        } else {
            btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }
};

// 复制文件链接的辅助函数
window.copyLink = (shortId, fileId, filename) => {
    let path;
    if (shortId && shortId !== 'None' && shortId !== '') {
        path = `/d/${shortId}`;
    } else {
        path = `/d/${fileId}/${encodeURIComponent(filename)}`;
    }
    Utils.copy(path);
};

// 认证系统
const Auth = {
    async logout() {
        if (!confirm('确定要退出登录吗？')) return;
        
        try {
            const res = await fetch('/api/auth/logout', {
                method: 'POST',
                // 确保携带凭证（Cookies）
                credentials: 'include' 
            });
            
            if (res.ok) {
                // 清理可能存在的本地状态
                // localStorage.removeItem('some_key'); 
                
                // 强制跳转到登录页，并替换历史记录，防止后退
                window.location.replace('/login');
            } else {
                Toast.show('退出失败，请刷新重试', 'error');
            }
        } catch (e) {
            console.error(e);
            Toast.show('网络错误', 'error');
        }
    }
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    Theme.init();
    
    // 侧边栏/移动端菜单切换

    const toggleBtn = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            if (overlay) overlay.classList.toggle('active');
        });
    }
    
    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }
});
