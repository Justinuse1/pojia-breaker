window.__ModuleLoader__.load({ id: "pojia-pilot", factory: (require) => {

		var module = { exports: {} };
		var exports = module.exports;
		Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
		let react = require("react");
		const h = react.createElement;
		const { useState, useEffect } = react;

		const name = "pojia-pilot";
		const inject = ["slots", "locale"];
		const API = "/pojiaai";

		async function api(path, opts) {
			const r = await fetch(API + path, {
				headers: { "Content-Type": "application/json" },
				...opts,
			});
			if (!r.ok) throw new Error(path + ": " + r.status);
			return r.json();
		}

		function StatusPanel() {
			const [st, setSt] = useState(null);
			const [err, setErr] = useState("");
			useEffect(() => {
				const tick = () => api("/status").then(setSt).catch((e) => setErr(e.message));
				tick();
				const iv = setInterval(tick, 5000);
				return () => clearInterval(iv);
			}, []);
			if (err) return h("div", { style: "color:#c55;padding:8px;" }, "pilot: " + err);
			if (!st) return h("div", { style: "padding:8px;color:#888;" }, "pilot loading…");
			return h("div", { style: "border:1px solid #2a6;border-radius:8px;padding:10px;margin:8px 0;background:#0d1a12;color:#cfc;font-size:13px;" },
				h("b", { style: "color:#4c8" }, "🎯 pojia-pilot"),
				h("div", null,
					"target: ", h("b", null, st.target || "-"),
					" · activated: ", st.activated ? "✅" : "no",
					" · passphrase: ", h("code", null, st.passphrase || "pojiaai")),
				h("div", { style: "color:#888;margin-top:4px" },
					"type passphrase in chat to activate; one-click recover on refusal"));
		}

		function RejectBar() {
			const [rej, setRej] = useState(null);
			useEffect(() => {
				const iv = setInterval(async () => {
					try {
						const s = await api("/guard");
						if (s.rejected) setRej(s); else setRej(null);
					} catch {}
				}, 4000);
				return () => clearInterval(iv);
			}, []);
			if (!rej) return null;
			return h("div", { style: "position:fixed;top:0;left:0;right:0;z-index:99999;background:#7a1f1f;color:#fff;padding:10px 16px;font-size:14px;display:flex;gap:12px;align-items:center;" },
				h("span", null, "🛡️ refusal detected (", rej.reason || "pattern", ")"),
				h("button", {
					style: "margin-left:auto;cursor:pointer;",
					onClick: async () => {
						try {
							const r = await api("/recover", { method: "POST", body: "{}" });
							setRej({ ...rej, recovered: true, reason: "archived " + (r.archived || "ok") + " — new session to resume" });
						} catch (e) { setRej({ ...rej, reason: "recover failed: " + e.message }); }
					}
				}, "archive & recover"),
				h("button", { style: "cursor:pointer;", onClick: () => setRej(null) }, "dismiss"));
		}

		function apply(ctx) {
			// 拒绝红条: 挂 conversation.input.right 旁的独立slot渲染
			ctx.slots.inject("settings.section", () => ctx.slots.register({
				name: "settings.section",
				id: "pojia-pilot",
				order: 30,
			}, StatusPanel));
			// 拒绝红条: 挂在会话输入右侧(固定可见位置)
			ctx.slots.inject("conversation.input.right", () => ctx.slots.register({
				name: "conversation.input.right",
				id: "pojia-pilot-guard",
				order: 50,
			}, RejectBar));
		}

		exports.name = name;
		exports.inject = inject;
		exports.apply = apply;
		return module.exports;
}});
