import { describe, it, expect } from 'vitest';
import { participantSchema, rsvpSchema, providerSchema } from './schemas';

// ── participantSchema ─────────────────────────────────────────────

describe('participantSchema', () => {
  it('validiert korrekte Eingabe', () => {
    const result = participantSchema.safeParse({ name: 'Max', email: 'max@test.de' });
    expect(result.success).toBe(true);
  });

  it('akzeptiert lange Namen', () => {
    const result = participantSchema.safeParse({ name: 'Max Mustermann', email: 'max@test.de' });
    expect(result.success).toBe(true);
  });

  it('verwirft zu kurzen Namen', () => {
    const result = participantSchema.safeParse({ name: 'M', email: 'max@test.de' });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.errors[0].message).toBe('Name muss mindestens 2 Zeichen lang sein');
    }
  });

  it('verwirdt ungültige Email', () => {
    const result = participantSchema.safeParse({ name: 'Max', email: 'invalid' });
    expect(result.success).toBe(false);
  });

  it('verwirdt zu langen Namen', () => {
    const longName = 'a'.repeat(101);
    const result = participantSchema.safeParse({ name: longName, email: 'max@test.de' });
    expect(result.success).toBe(false);
  });

  it('verwirdt leere Eingabe', () => {
    const result = participantSchema.safeParse({ name: '', email: '' });
    expect(result.success).toBe(false);
  });
});

// ── rsvpSchema ────────────────────────────────────────────────────

describe('rsvpSchema', () => {
  it('validiert korrekte Antwort ohne Begleitung', () => {
    const result = rsvpSchema.safeParse({ response: 'yes', companions: 0 });
    expect(result.success).toBe(true);
  });

  it('validiert Antwort mit Begleitung', () => {
    const result = rsvpSchema.safeParse({ response: 'yes', companions: 1 });
    expect(result.success).toBe(true);
  });

  it('verwirdt zu viele Begleitungen', () => {
    const result = rsvpSchema.safeParse({ response: 'yes', companions: 2 });
    expect(result.success).toBe(false);
  });

  it('verwirdt negative Begleitungen', () => {
    const result = rsvpSchema.safeParse({ response: 'yes', companions: -1 });
    expect(result.success).toBe(false);
  });

  it('akzeptiert "maybe" als Antwort', () => {
    const result = rsvpSchema.safeParse({ response: 'maybe', companions: 0 });
    expect(result.success).toBe(true);
  });

  it('akzeptiert "no" als Antwort', () => {
    const result = rsvpSchema.safeParse({ response: 'no', companions: 0 });
    expect(result.success).toBe(true);
  });

  it('verwirdt ungültige Antwort', () => {
    const result = rsvpSchema.safeParse({ response: 'invalid', companions: 0 });
    expect(result.success).toBe(false);
  });
});

// ── providerSchema ────────────────────────────────────────────────

describe('providerSchema', () => {
  it('validiert korrekten Provider', () => {
    const result = providerSchema.safeParse({ name: 'Pension Schmidt', url: 'https://pension.de' });
    expect(result.success).toBe(true);
  });

  it('verwirdt zu kurzen Namen', () => {
    const result = providerSchema.safeParse({ name: 'A', url: 'https://pension.de' });
    expect(result.success).toBe(false);
  });

  it('verwirdt ungültige URL', () => {
    const result = providerSchema.safeParse({ name: 'Pension Schmidt', url: 'nicht-eine-url' });
    expect(result.success).toBe(false);
  });

  it('akzeptiert verschiedene URL-Formate', () => {
    const result = providerSchema.safeParse({ name: 'Test', url: 'https://example.com/programm' });
    expect(result.success).toBe(true);
  });
});
