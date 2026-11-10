"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Compass, Lock, Mail, User, ShieldCheck, ArrowRight, Key, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("analyst@jatayuv.ai");
  const [password, setPassword] = useState("jatayuv2026");
  const [fullName, setFullName] = useState("Commander V. Sharma");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      if (isRegister) {
        await api.register({ email, password, full_name: fullName });
      }
      const res = await api.loginJson({ email, password });
      if (res && res.access_token) {
        localStorage.setItem("jatayuv_token", res.access_token);
      }
      router.push("/dashboard");
    } catch (err: any) {
      const msg = err?.message || (isRegister ? "Registration failed." : "Authentication failed. Invalid email or password.");
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemo = () => {
    setEmail("analyst@jatayuv.ai");
    setPassword("jatayuv2026");
    setError(null);
  };

  return (
    <div className="flex-1 flex items-center justify-center p-6 min-h-[calc(100vh-3.5rem)] bg-forest-950 font-mono text-xs">
      <div className="w-full max-w-md glass-panel p-8 rounded-xl border border-emerald-500/25 shadow-2xl relative">
        {/* Tactical HUD Corner Elements */}
        <div className="hud-corner-tl" />
        <div className="hud-corner-tr" />
        <div className="hud-corner-bl" />
        <div className="hud-corner-br" />

        <div className="text-center pb-6 border-b border-emerald-500/15">
          <div className="mx-auto w-12 h-12 rounded-lg bg-forest-900 border border-emerald-500/40 text-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-950/60 mb-3">
            <Compass className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-black text-white tracking-wider">
            {isRegister ? "REGISTER ANALYST" : "MISSION CONTROL SIGN IN"}
          </h2>
          <p className="text-[11px] text-muted-foreground mt-1">
            {isRegister
              ? "Register credential hash to local database schema."
              : "Authenticate to access UAV flight logs, telemetry, and 3D models."}
          </p>
        </div>

        {/* Demo Credentials Quick Pill */}
        <div className="mt-4 p-3 rounded bg-forest-900/90 border border-emerald-500/20 text-[11px] space-y-1">
          <div className="flex items-center justify-between text-emerald-400 font-bold">
            <span className="flex items-center gap-1">
              <Key className="w-3.5 h-3.5" /> SEED ANALYST CREDENTIALS
            </span>
            <button
              type="button"
              onClick={fillDemo}
              className="text-[10px] text-muted-foreground hover:text-white underline"
            >
              PRE-FILL
            </button>
          </div>
          <div className="text-muted-foreground">User: <span className="text-white">analyst@jatayuv.ai</span></div>
          <div className="text-muted-foreground">Pass: <span className="text-white">jatayuv2026</span></div>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-5">
          {error && (
            <div className="p-2.5 rounded bg-rose-950/80 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}

          {isRegister && (
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] uppercase tracking-wider text-muted-foreground">Analyst Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Commander V. Sharma"
                  className="w-full pl-9 pr-3 py-2 bg-forest-950 border border-emerald-500/30 rounded text-xs text-white placeholder:text-muted-foreground focus:outline-none focus:border-emerald-400"
                />
              </div>
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground">Mission Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@jatayuv.ai"
                className="w-full pl-9 pr-3 py-2 bg-forest-950 border border-emerald-500/30 rounded text-xs text-white placeholder:text-muted-foreground focus:outline-none focus:border-emerald-400"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground">Access Key / Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 bg-forest-950 border border-emerald-500/30 rounded text-xs text-white placeholder:text-muted-foreground focus:outline-none focus:border-emerald-400"
              />
            </div>
          </div>

          <Button type="submit" variant="primary" size="md" isLoading={isLoading} className="mt-2 w-full">
            {isRegister ? "Register Account" : "Access Mission Control"}{" "}
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>

          <div className="text-center text-[11px] text-muted-foreground pt-3 border-t border-emerald-500/15">
            {isRegister ? (
              <span>
                Already registered?{" "}
                <button
                  type="button"
                  onClick={() => setIsRegister(false)}
                  className="text-emerald-400 font-bold hover:underline ml-1"
                >
                  Sign In
                </button>
              </span>
            ) : (
              <span>
                Need new mission credentials?{" "}
                <button
                  type="button"
                  onClick={() => setIsRegister(true)}
                  className="text-emerald-400 font-bold hover:underline ml-1"
                >
                  Register
                </button>
              </span>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
