export interface BillingInfo {
  userId: string;
  subscriptionType: 'free' | 'monthly' | 'annual';
  startDate: Date;
  endDate: Date;
  isActive: boolean;
  paymentMethod: 'credit_card' | 'paypal' | 'bank_transfer';
  amountPaid: number;
  currency: string;
}

export interface PaymentHistory {
  transactionId: string;
  userId: string;
  amount: number;
  currency: string;
  date: Date;
  status: 'completed' | 'pending' | 'failed';
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  duration: 'monthly' | 'annual';
  features: string[];
}