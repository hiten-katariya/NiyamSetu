import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
}

const FAQS: FAQItem[] = [
  {
    question: 'What is NiyamSetu?',
    answer:
      'NiyamSetu is an institutional workflow orchestration and compliance monitoring platform designed to support AICTE approval processes. It unifies application lifecycle management, scrutiny tracking, Expert Visit Committee (EVC) scheduling, time-bound compliance undertakings, document validity monitoring, and cryptographic auditability in a single system.',
  },
  {
    question: 'Who can use NiyamSetu?',
    answer:
      'NiyamSetu is designed for authorized stakeholders across 7 specific roles: Institutional Administrators, Scrutiny Officers, Regional Officers, Expert Committee Members, Bureau Officers, Senior Authorities, and System Administrators. Public visitors may browse this overview, but access to internal files and applications requires verified institutional credentials.',
  },
  {
    question: 'How does the platform support application workflows?',
    answer:
      'When an application is created, it is pinned to an active workflow route version. The application advances through sequential stages (such as Drafting, Document Scrutiny, EVC, and Approval) only when authorized role holders complete required verification actions. Deficiencies require mandatory written justification, and regulatory holds temporarily pause SLA clocks without disrupting the audit trail.',
  },
  {
    question: 'How are documents and compliance obligations tracked?',
    answer:
      'The platform maintains an institutional document vault where certificates (such as land leases, structural stability, and fire safety NOCs) are registered with validity start and end dates. Proactive notifications alert institutions before expiration. Similarly, conditional approval undertakings are tracked against target dates, requiring evidence uploads and dual-control officer signoff before being marked fulfilled.',
  },
  {
    question: 'Does NiyamSetu make statutory approval decisions automatically?',
    answer:
      'No. Under no circumstances does NiyamSetu autonomously grant, deny, or replace statutory AICTE approvals. The platform provides workflow management, pendency monitoring, automated reminders, and documentation checks. All regulatory inspections, scrutiny evaluations, and approval decisions remain exclusively with authorized human officials and councils.',
  },
  {
    question: 'How is access to institutional information controlled?',
    answer:
      'NiyamSetu enforces strict server-side tenant isolation. Institutional users can only view and manage records belonging to their registered institution. Regional officers are scoped strictly to institutions within their geographical jurisdiction. All document downloads stream through permission-checked endpoints, and every state mutation is recorded in an append-only, SHA-256 hash-chained audit ledger.',
  },
  {
    question: 'How can an authorized user sign in?',
    answer:
      'Authorized personnel can click the "Sign In" button in the navigation header or visit the login route directly. Credentials (email and password) are authenticated via secure HTTP-only cookies with CSRF token verification and rate limiting. Contact your institutional administrator or regional AICTE office for account provisioning.',
  },
];

export const FaqSection: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggleFaq = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="py-24 bg-white border-t border-niyam-border/70" id="faq">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <span className="text-xs font-bold text-niyam-primary uppercase tracking-widest bg-niyam-primary-tint px-3 py-1 rounded-full">
            Frequently Asked Questions
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight mt-4">
            Answers &amp; Technical Governance
          </h2>
          <p className="mt-4 text-base sm:text-lg text-niyam-text-muted leading-relaxed">
            Essential information regarding access policies, operational mechanics, and statutory decision boundaries in NiyamSetu.
          </p>
        </div>

        {/* Accordion List */}
        <div className="max-w-3xl mx-auto divide-y divide-niyam-border/80 border-y border-niyam-border/80">
          {FAQS.map((faq, index) => {
            const isOpen = openIndex === index;
            return (
              <div key={index} className="py-5">
                <button
                  type="button"
                  onClick={() => toggleFaq(index)}
                  className="w-full flex items-center justify-between text-left gap-4 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-niyam-focus rounded-lg p-1"
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${index}`}
                >
                  <span className="text-base sm:text-lg font-bold text-niyam-text group-hover:text-niyam-primary transition-colors">
                    {faq.question}
                  </span>
                  <div
                    className={`w-8 h-8 rounded-full bg-niyam-surface-alt flex items-center justify-center shrink-0 transition-transform duration-200 ${
                      isOpen ? 'rotate-180 bg-niyam-primary text-white' : 'text-niyam-text-muted'
                    }`}
                  >
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </button>

                {isOpen && (
                  <div
                    id={`faq-answer-${index}`}
                    className="mt-3.5 pr-8 text-sm text-niyam-text-muted leading-relaxed animate-in fade-in-50 duration-200"
                  >
                    <p>{faq.answer}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
