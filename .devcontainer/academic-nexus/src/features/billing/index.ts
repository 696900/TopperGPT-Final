import { useState, useEffect } from 'react';
import { BillingInfo, PaymentMethod } from '../../types/billing';

const useBilling = () => {
  const [billingInfo, setBillingInfo] = useState<BillingInfo | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBillingInfo = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/billing/info');
        if (!response.ok) {
          throw new Error('Failed to fetch billing information');
        }
        const data = await response.json();
        setBillingInfo(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    const fetchPaymentMethods = async () => {
      try {
        const response = await fetch('/api/billing/payment-methods');
        if (!response.ok) {
          throw new Error('Failed to fetch payment methods');
        }
        const data = await response.json();
        setPaymentMethods(data);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchBillingInfo();
    fetchPaymentMethods();
  }, []);

  return {
    billingInfo,
    paymentMethods,
    loading,
    error,
  };
};

export default useBilling;