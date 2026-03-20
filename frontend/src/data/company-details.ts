import { Company } from "./types";

// Extended company data for company profile pages
export const companyDetails: Record<string, {
  founded: string;
  size: string;
  hq: string;
  description: string;
  locations: string[];
}> = {
  c1: {
    founded: "2019",
    size: "200–500",
    hq: "Dubai, UAE",
    description: "TechNova is an AI-driven SaaS platform serving 500+ enterprise clients across the MENA region. We build intelligent analytics and automation tools that help businesses make data-driven decisions. Our engineering culture values clean code, continuous learning, and user-centric design. We operate offices in Dubai, Riyadh, and Amman, with a distributed remote team spanning 8 countries.",
    locations: ["Dubai, UAE", "Riyadh, KSA", "Amman, Jordan", "Remote"],
  },
  c2: {
    founded: "2021",
    size: "50–200",
    hq: "Cairo, Egypt",
    description: "FinEdge is a fintech startup revolutionizing cross-border payments in the Arab world. We provide instant, low-cost transfers for individuals and businesses. Our platform processes over $200M in monthly transactions and serves users in 12 countries.",
    locations: ["Cairo, Egypt", "Riyadh, KSA"],
  },
  c3: {
    founded: "2018",
    size: "100–300",
    hq: "Jeddah, KSA",
    description: "MedCare Plus is a digital health platform connecting patients with specialists across the GCC. We combine telemedicine, e-pharmacy, and health records into a seamless experience. Trusted by 50,000+ patients.",
    locations: ["Jeddah, KSA", "Kuwait City, Kuwait"],
  },
  c4: {
    founded: "2020",
    size: "30–80",
    hq: "Remote-first",
    description: "EduSpark is an EdTech company offering Arabic-first online learning experiences. We design STEM curricula for K-12 students, partnering with ministries of education across 5 countries to bridge the digital learning gap.",
    locations: ["Remote"],
  },
  c5: {
    founded: "2015",
    size: "80–150",
    hq: "Dubai, UAE",
    description: "BrandWave is a full-service digital marketing agency with offices in Dubai, Cairo, and Beirut. We craft compelling brand stories and execute high-impact campaigns for 100+ MENA brands across all digital channels.",
    locations: ["Dubai, UAE", "Cairo, Egypt", "Beirut, Lebanon"],
  },
  c6: {
    founded: "2010",
    size: "500–1000",
    hq: "Abu Dhabi, UAE",
    description: "BuildRight is a leading civil engineering and construction firm with landmark projects across the GCC. With 13 years of experience, we specialize in commercial, residential, and infrastructure development with a focus on sustainable building practices.",
    locations: ["Abu Dhabi, UAE", "Doha, Qatar"],
  },
  c7: {
    founded: "2017",
    size: "20–50",
    hq: "Amman, Jordan",
    description: "PixelCraft is an award-winning UX/UI design studio based in Amman. We partner with startups and enterprises to create beautiful, user-centered digital products. Our portfolio includes 200+ projects across 15 industries.",
    locations: ["Amman, Jordan"],
  },
  c8: {
    founded: "2022",
    size: "30–80",
    hq: "Dubai, UAE",
    description: "SalesForce Arabia is a B2B sales enablement platform built specifically for the MENA market. We provide CRM tools, pipeline management, and analytics to help sales teams close more deals. Serving 300+ businesses across the GCC and Egypt.",
    locations: ["Dubai, UAE", "Cairo, Egypt"],
  },
};
