export default function Footer() {
  return (
    <footer className="w-full border-t border-border bg-card p-4 mt-auto">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-2 text-sm text-text-secondary text-center md:text-left">
        <p>© {new Date().getFullYear()} Medical Diagnostic Systems. All rights reserved.</p>
        <div className="flex items-center gap-4">
          <a className="hover:text-primary transition-colors hover:underline" href="#">
            Privacy Policy
          </a>
          <a className="hover:text-primary transition-colors hover:underline" href="#">
            Terms of Service
          </a>
          <a className="hover:text-primary transition-colors hover:underline" href="#">
            Support
          </a>
        </div>
      </div>
    </footer>
  );
}
