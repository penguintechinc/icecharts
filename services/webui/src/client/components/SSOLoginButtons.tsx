import React, { useEffect, useState } from 'react';
import Button from './Button';

interface SSOProvider {
  type: 'saml' | 'oidc';
  id: string;
  name: string;
  icon?: string;
}

interface SSOStatus {
  saml_available: boolean;
  oidc_available: boolean;
  configured_providers: SSOProvider[];
}

interface SSOLoginButtonsProps {
  onSSOLogin?: (provider: SSOProvider) => void;
}

export default function SSOLoginButtons({ onSSOLogin }: SSOLoginButtonsProps) {
  const [ssoStatus, setSsoStatus] = useState<SSOStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSSOStatus();
  }, []);

  const fetchSSOStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/sso/status');

      if (!response.ok) {
        throw new Error('Failed to fetch SSO status');
      }

      const data = await response.json();
      setSsoStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setSsoStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSAMLLogin = () => {
    // Redirect to SAML login endpoint
    const provider: SSOProvider = {
      type: 'saml',
      id: 'default-saml',
      name: 'SAML',
    };

    if (onSSOLogin) {
      onSSOLogin(provider);
    }

    window.location.href = '/api/v1/sso/saml/login';
  };

  const handleOIDCLogin = () => {
    // Redirect to OIDC login endpoint
    const provider: SSOProvider = {
      type: 'oidc',
      id: 'default-oidc',
      name: 'OIDC',
    };

    if (onSSOLogin) {
      onSSOLogin(provider);
    }

    window.location.href = '/api/v1/sso/oidc/login';
  };

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="h-10 bg-dark-800 rounded animate-pulse"></div>
        <div className="h-10 bg-dark-800 rounded animate-pulse"></div>
      </div>
    );
  }

  if (!ssoStatus || (!ssoStatus.saml_available && !ssoStatus.oidc_available)) {
    return null;
  }

  return (
    <div className="space-y-3">
      {error && (
        <div className="p-2 bg-red-900/30 border border-red-700 rounded text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="text-center text-sm text-dark-400 mb-3">
        Enterprise Single Sign-On
      </div>

      {ssoStatus.saml_available && (
        <Button
          onClick={handleSAMLLogin}
          className="w-full bg-blue-600 hover:bg-blue-700"
          variant="secondary"
        >
          Sign in with SAML
        </Button>
      )}

      {ssoStatus.oidc_available && (
        <Button
          onClick={handleOIDCLogin}
          className="w-full bg-green-600 hover:bg-green-700"
          variant="secondary"
        >
          Sign in with OIDC
        </Button>
      )}

      <div className="relative my-3">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-dark-700"></div>
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="px-2 bg-dark-950 text-dark-500">Or</span>
        </div>
      </div>
    </div>
  );
}
