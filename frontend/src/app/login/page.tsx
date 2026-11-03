"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Compass, Lock, Mail, User, ShieldCheck, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("analyst@jatayuv.ai");
  const [password, setPassword] = useState("jatayuv2026");
  const [fullName, setFullName] = useState("Lead Flight Analyst");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      window.location.href = "/";
    }, 1000);
  };

  return (
    <div className="flex-1 flex items-center justify-center p-6 min-h-[calc(100vh-4rem)]">
      <Card className="w-full max-w-md border-border bg-card/90 backdrop-blur shadow-xl">
        <CardHeader className="text-center pb-4">
          <div className="mx-auto w-12 h-12 rounded-xl bg-gradient-to-tr from-sky-600 to-primary text-white flex items-center justify-center shadow-lg shadow-primary/20 mb-2">
            <Compass className="w-7 h-7" />
          </div>
          <CardTitle className="text-xl font-bold text-white">
            {isRegister ? "Create Analyst Account" : "Sign In to JATAYUV-AI"}
          </CardTitle>
          <CardDescription className="text-xs">
            {isRegister
              ? "Join the autonomous aerial photogrammetry and spatial AI platform."
              : "Enter your credentials to access mission datasets and AI models."}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {isRegister && (
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Dr. Rajesh Rao"
                    className="w-full pl-9 pr-3 py-2 bg-secondary/50 border border-border rounded-lg text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>
            )}

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Corporate / Mission Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@jatayuv.ai"
                  className="w-full pl-9 pr-3 py-2 bg-secondary/50 border border-border rounded-lg text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Secure Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 bg-secondary/50 border border-border rounded-lg text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            <Button type="submit" variant="primary" size="md" isLoading={isLoading} className="mt-2 w-full">
              {isRegister ? "Create Account" : "Access Mission Control"}{" "}
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>

            <div className="text-center text-xs text-muted-foreground mt-3 pt-3 border-t border-border">
              {isRegister ? (
                <span>
                  Already registered?{" "}
                  <button
                    type="button"
                    onClick={() => setIsRegister(false)}
                    className="text-primary hover:underline font-semibold"
                  >
                    Sign In
                  </button>
                </span>
              ) : (
                <span>
                  Need mission credentials?{" "}
                  <button
                    type="button"
                    onClick={() => setIsRegister(true)}
                    className="text-primary hover:underline font-semibold"
                  >
                    Request Analyst Access
                  </button>
                </span>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
