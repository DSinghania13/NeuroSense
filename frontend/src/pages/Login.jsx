import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { ROUTES } from '../constants/routes';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';

const SECURITY_QUESTIONS = [
  "What was the name of your first pet?",
  "In what city were you born?",
  "What is your mother's maiden name?",
  "What was your childhood nickname?",
  "What city did you attend medical school in?"
];

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register } = useAuth();
  const { notify } = useNotification();

  const [mode, setMode] = useState('login');
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    specialty: '',
    clinic_name: '',
    security_question: SECURITY_QUESTIONS[0],
    security_answer: ''
  });

  const from = location.state?.from?.pathname || ROUTES.DASHBOARD;

  useEffect(() => {
    fetch('/api/warmup').catch(err => console.log("Warmup ping failed"));
  }, []);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(formData.email, formData.password);
      notify("Welcome Back", "Authentication successful.", "success");
      navigate(from, { replace: true });
    } catch (err) {
      notify("Login Failed", err.message, "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterProgress = async (e) => {
    e.preventDefault();

    if (step === 1) {
      if (formData.password !== formData.confirmPassword) {
        notify("Password Mismatch", "Your passwords do not match.", "error");
        return;
      }
      if (formData.password.length < 6) {
        notify("Weak Password", "Password must be at least 6 characters.", "error");
        return;
      }
      setStep(2);
    }
    else if (step === 2) {
      if (!formData.security_answer.trim()) {
        notify("Required", "Please provide an answer to your security question.", "error");
        return;
      }
      setStep(3);
    }
    else if (step === 3) {
      setIsLoading(true);
      try {
        await register(formData);
        notify("Account Created", "Your clinical profile is ready.", "success");
        navigate(from, { replace: true });
      } catch (err) {
        notify("Registration Failed", err.message, "error");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    if (step === 1) {
      try {
        const res = await fetch('/api/auth/security-question', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: formData.email })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        handleChange('security_question', data.question);
        setStep(2);
      } catch (err) {
        notify("Error", err.message, "error");
      } finally {
        setIsLoading(false);
      }
    }
    else if (step === 2) {
      if (formData.password !== formData.confirmPassword) {
        notify("Password Mismatch", "Your new passwords do not match.", "error");
        setIsLoading(false);
        return;
      }

      try {
        const res = await fetch('/api/auth/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            security_answer: formData.security_answer,
            new_password: formData.password
          })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        notify("Password Reset", "Your password has been successfully updated. Please sign in.", "success");
        setMode('login');
        setFormData(prev => ({ ...prev, password: '', confirmPassword: '', security_answer: '' }));
      } catch (err) {
        notify("Verification Failed", err.message, "error");
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#e8f0fe] via-[#f4f6f8] to-[#dce8f5] relative overflow-hidden">
      <div className="relative z-10 w-full max-w-md px-4 py-8">
        <div className="bg-card rounded-2xl shadow-2xl border border-border/50 p-8 md:p-10 backdrop-blur-sm">

          <div className="flex flex-col items-center mb-6">
            <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-primary text-white mb-4 shadow-lg shadow-primary/30">
              <span className="material-symbols-outlined text-4xl">neurology</span>
            </div>
            <h1 className="text-2xl font-black text-text-primary tracking-tight">NeuroSense</h1>
            <p className="text-text-secondary text-sm mt-1 text-center">
              {mode === 'login' && "Clinical Authentication Portal"}
              {mode === 'register' && `Account Setup - Step ${step} of 3`}
              {mode === 'forgot' && "Account Recovery"}
            </p>
          </div>

          {/* ======================================= */}
          {/* LOGIN MODE */}
          {/* ======================================= */}
          {mode === 'login' && (
            <form onSubmit={handleLogin} className="flex flex-col gap-5">
              <Input id="email" type="email" label="Email Address" icon="mail" placeholder="doctor@hospital.com" value={formData.email} onChange={(e) => handleChange('email', e.target.value)} required />

              <div className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-bold text-text-primary">Password</label>
                  <button type="button" onClick={() => { setMode('forgot'); setStep(1); }} className="text-xs text-primary hover:underline font-medium">Forgot password?</button>
                </div>
                <div className="relative">
                  <Input id="password" type={showPassword ? 'text' : 'password'} icon="lock" placeholder="••••••••" value={formData.password} onChange={(e) => handleChange('password', e.target.value)} className="pr-12" wrapperClassName="w-full" required />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-primary flex items-center justify-center">
                    <span className="material-symbols-outlined text-xl">{showPassword ? 'visibility_off' : 'visibility'}</span>
                  </button>
                </div>
              </div>

              <Button type="submit" disabled={isLoading} className="h-12 w-full mt-2">
                {isLoading ? "Authenticating..." : "Sign In"}
              </Button>

              <p className="text-sm text-center mt-4 text-text-secondary">
                New physician? <button type="button" onClick={() => { setMode('register'); setStep(1); }} className="text-primary font-bold hover:underline">Create an Account</button>
              </p>
            </form>
          )}

          {/* ======================================= */}
          {/* REGISTER WIZARD */}
          {/* ======================================= */}
          {mode === 'register' && (
            <form onSubmit={handleRegisterProgress} className="flex flex-col gap-5">

              {/* STEP 1: Credentials */}
              {step === 1 && (
                <>
                  <Input id="reg-email" type="email" label="Email Address" icon="mail" placeholder="doctor@hospital.com" value={formData.email} onChange={(e) => handleChange('email', e.target.value)} required />
                  <Input id="reg-pass" type="password" label="Create Password" icon="lock" placeholder="••••••••" value={formData.password} onChange={(e) => handleChange('password', e.target.value)} required />
                  <Input id="reg-confirm" type="password" label="Confirm Password" icon="lock" placeholder="••••••••" value={formData.confirmPassword} onChange={(e) => handleChange('confirmPassword', e.target.value)} required />
                </>
              )}

              {/* STEP 2: Security */}
              {step === 2 && (
                <>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-sm font-bold text-text-primary">Security Question</label>
                    <div className="relative flex items-center">
                      <select
                        value={formData.security_question}
                        onChange={(e) => handleChange('security_question', e.target.value)}
                        className="w-full appearance-none rounded-lg border border-border bg-background py-3 pl-10 pr-10 text-text-primary focus:ring-2 focus:ring-primary outline-none"
                      >
                        {SECURITY_QUESTIONS.map(q => <option key={q} value={q}>{q}</option>)}
                      </select>
                      <span className="material-symbols-outlined absolute left-3 text-text-secondary pointer-events-none">help</span>
                      <span className="material-symbols-outlined absolute right-3 text-text-secondary pointer-events-none">expand_more</span>
                    </div>
                  </div>
                  <Input id="reg-answer" type="text" label="Your Answer" icon="key" placeholder="e.g. Fluffy or Boston" value={formData.security_answer} onChange={(e) => handleChange('security_answer', e.target.value)} required />
                  <p className="text-xs text-text-secondary mt-1">This answer will be securely encrypted. You will need it if you ever forget your password.</p>
                </>
              )}

              {/* STEP 3: Profile */}
              {step === 3 && (
                <>
                  <Input id="reg-name" type="text" label="Full Name (Dr.)" icon="person" placeholder="e.g. Dr. Jane Doe" value={formData.name} onChange={(e) => handleChange('name', e.target.value)} required />
                  <Input id="reg-spec" type="text" label="Medical Specialty" icon="medical_services" placeholder="e.g. Neurologist" value={formData.specialty} onChange={(e) => handleChange('specialty', e.target.value)} required />
                  <Input id="reg-clinic" type="text" label="Clinic / Hospital Name" icon="local_hospital" placeholder="e.g. Mercy Hospital" value={formData.clinic_name} onChange={(e) => handleChange('clinic_name', e.target.value)} required />
                </>
              )}

              <div className="flex gap-3 mt-4">
                {step > 1 && (
                  <Button type="button" variant="outline" onClick={() => setStep(step - 1)} className="flex-1">Back</Button>
                )}
                <Button type="submit" disabled={isLoading} className="flex-2 w-full">
                  {isLoading ? "Processing..." : (step === 3 ? "Complete Setup" : "Continue")}
                </Button>
              </div>

              <p className="text-sm text-center mt-2 text-text-secondary">
                Already registered? <button type="button" onClick={() => setMode('login')} className="text-primary font-bold hover:underline">Sign In</button>
              </p>
            </form>
          )}

          {/* ======================================= */}
          {/* FORGOT PASSWORD WIZARD */}
          {/* ======================================= */}
          {mode === 'forgot' && (
            <form onSubmit={handleForgotPassword} className="flex flex-col gap-5">

              {/* STEP 1: Find Account */}
              {step === 1 && (
                <>
                  <p className="text-sm text-text-secondary mb-2 text-center">Enter your email address to pull up your security verification question.</p>
                  <Input id="forgot-email" type="email" label="Account Email Address" icon="mail" placeholder="doctor@hospital.com" value={formData.email} onChange={(e) => handleChange('email', e.target.value)} required />
                </>
              )}

              {/* STEP 2: Answer & Reset */}
              {step === 2 && (
                <>
                  <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                    <p className="text-xs font-bold text-primary uppercase tracking-wider mb-1">Security Question</p>
                    <p className="text-text-primary font-medium">{formData.security_question}</p>
                  </div>
                  <Input id="forgot-answer" type="text" label="Your Answer" icon="key" placeholder="Enter your secret answer" value={formData.security_answer} onChange={(e) => handleChange('security_answer', e.target.value)} required />

                  <div className="border-t border-border my-2" />

                  <Input id="forgot-newpass" type="password" label="New Password" icon="lock" placeholder="••••••••" value={formData.password} onChange={(e) => handleChange('password', e.target.value)} required />
                  <Input id="forgot-confirmpass" type="password" label="Confirm New Password" icon="lock" placeholder="••••••••" value={formData.confirmPassword} onChange={(e) => handleChange('confirmPassword', e.target.value)} required />
                </>
              )}

              <Button type="submit" disabled={isLoading} className="h-12 w-full mt-2">
                {isLoading ? "Verifying..." : (step === 1 ? "Find Account" : "Reset Password")}
              </Button>

              <button type="button" onClick={() => setMode('login')} className="text-sm text-text-secondary hover:text-primary mt-4 font-medium transition-colors">
                Cancel & Return to Login
              </button>
            </form>
          )}

        </div>
      </div>
    </div>
  );
}