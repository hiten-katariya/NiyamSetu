import React, { useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { TrustStrip } from './components/TrustStrip';
import { ShowcaseSection } from './components/ShowcaseSection';
import { PlatformOverview } from './components/PlatformOverview';
import { CapabilitiesBento } from './components/CapabilitiesBento';
import { WorkflowTimeline } from './components/WorkflowTimeline';
import { SecuritySection } from './components/SecuritySection';
import { InteractivePreview } from './components/InteractivePreview';
import { StakeholderBenefits } from './components/StakeholderBenefits';
import { FaqSection } from './components/FaqSection';
import { FinalCta } from './components/FinalCta';
import { Footer } from './components/Footer';

export const LandingPage: React.FC = () => {
  useEffect(() => {
    // Set page title for public visitor
    document.title = 'NiyamSetu — AICTE Workflow & Institutional Compliance Platform';
  }, []);

  return (
    <div className="min-h-screen bg-niyam-bg text-niyam-text selection:bg-niyam-primary-tint selection:text-niyam-primary">
      {/* Sticky Glass Navbar */}
      <Navbar />

      <main>
        {/* Hero Section */}
        <Hero />

        {/* 4 Pillars Trust Strip */}
        <TrustStrip />

        {/* 3D Circular Carousel Interactive Module Showcase */}
        <ShowcaseSection />

        {/* Platform Architecture & Interconnection Overview */}
        <PlatformOverview />

        {/* Capabilities Bento Grid */}
        <CapabilitiesBento />

        {/* 6-Stage Workflow Timeline */}
        <WorkflowTimeline />

        {/* Security & Multi-Tenant Governance */}
        <SecuritySection />

        {/* Role-Adapted Interactive Interface Preview */}
        <InteractivePreview />

        {/* Benefits by Stakeholder Persona */}
        <StakeholderBenefits />

        {/* FAQ Accordion */}
        <FaqSection />

        {/* Final Call to Action */}
        <FinalCta />
      </main>

      {/* Institutional Footer */}
      <Footer />
    </div>
  );
};

export default LandingPage;
