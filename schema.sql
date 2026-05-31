-- PocketPal Database Schema
-- Run this in your Supabase SQL Editor:
-- https://supabase.com/dashboard/project/zgnnxujzbjohaovsfuhj/sql/new

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Expenses Table ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.expenses (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    amount      NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    description TEXT NOT NULL,
    category    TEXT NOT NULL CHECK (category IN ('Food', 'Travel', 'Shopping', 'Recharge', 'Petrol', 'Others')),
    date        DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON public.expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date    ON public.expenses(date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON public.expenses(category);

-- ─── Debts Table ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.debts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('borrowed', 'lent')),
    person      TEXT NOT NULL,
    amount      NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    note        TEXT,
    due_date    DATE,
    status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_debts_user_id ON public.debts(user_id);

-- ─── Budget Limits Table ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.budget_limits (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    category     TEXT NOT NULL CHECK (category IN ('Food', 'Travel', 'Shopping', 'Recharge', 'Petrol', 'Others')),
    limit_amount NUMERIC(12, 2) NOT NULL CHECK (limit_amount >= 0),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, category)
);

CREATE INDEX IF NOT EXISTS idx_budget_limits_user ON public.budget_limits(user_id);

-- ─── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE public.expenses      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.debts         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budget_limits ENABLE ROW LEVEL SECURITY;

-- Expenses: each user sees only their own
DROP POLICY IF EXISTS "Users manage own expenses" ON public.expenses;
CREATE POLICY "Users manage own expenses"
ON public.expenses FOR ALL TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Debts: each user sees only their own
DROP POLICY IF EXISTS "Users manage own debts" ON public.debts;
CREATE POLICY "Users manage own debts"
ON public.debts FOR ALL TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Budget Limits: each user sees only their own
DROP POLICY IF EXISTS "Users manage own budget limits" ON public.budget_limits;
CREATE POLICY "Users manage own budget limits"
ON public.budget_limits FOR ALL TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- ─── Enable Realtime ──────────────────────────────────────────────────────────
-- Run only once; ignore errors if already added
DO $$
BEGIN
  BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE public.expenses;
  EXCEPTION WHEN others THEN NULL;
  END;
  BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE public.debts;
  EXCEPTION WHEN others THEN NULL;
  END;
  BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE public.budget_limits;
  EXCEPTION WHEN others THEN NULL;
  END;
END $$;
