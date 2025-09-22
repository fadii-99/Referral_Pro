// Icons import
import Agriculture from './../assets/Industries/agriculture.png';
import ApparelGoods from './../assets/Industries/Apparel&Goods.png';
import ArtCommunity from './../assets/Industries/Art&Community.png';
import BeautyWellness from './../assets/Industries/Beauty&Wellness.png';
import BusinessServices from './../assets/Industries/BusinessServices.png';
import CreativeDigital from './../assets/Industries/Creative&Digital.png';
import EventsEntertainment from './../assets/Industries/Events&Entertainment.png';
import FoodBeverage from './../assets/Industries/Food&Beverage.png';
import HomeProperty from './../assets/Industries/Home&Property.png';
import KidsEducation from './../assets/Industries/Kids&Education.png';
import Logistics from './../assets/Industries/Logistics.png';
import Manufacturing from './../assets/Industries/Manufacturing.png';
import Pets from './../assets/Industries/Pets.png';
import RealEstate from './../assets/Industries/RealEstate.png';
import Security from './../assets/Industries/Security.png';
import TechnologyIT from './../assets/Industries/Technology&IT.png';
import TravelLifestyle from './../assets/Industries/Travel&Lifestyle.png';
import VehicleMobility from './../assets/Industries/Vehicle&Mobility.png';

// Specialty ka icon missing → placeholder
import IndustryLogo from './../assets/figmaIcons/industry.png';

export interface Category {
  category: string;
  icon: string;
  subcategories: string[];
}

export const categories: Category[] = [
  {
    category: "Home & Property",
    icon: HomeProperty,
    subcategories: [
      "General contractors", "Handyman services", "Electricians", "Plumbers", "HVAC",
      "Roofing", "Flooring", "Windows & doors", "Painting", "Landscaping", "Pools",
      "Pest control", "Fencing", "Garage services", "Cleaning services", "Junk removal",
      "Home organizing", "Security systems", "Interior design", "Property management",
      "Pressure washing", "Stone & masonry"
    ]
  },
  {
    category: "Vehicles & Mobility",
    icon: VehicleMobility,
    subcategories: [
      "Auto repair", "Tire shop", "Car audio & wraps", "Mobile mechanics", "Motorcycle services",
      "Boat & marine services", "RV services", "Towing", "Driving schools"
    ]
  },
  {
    category: "Real Estate–Adjacent",
    icon: RealEstate,
    subcategories: [
      "Realtors (commercial)", "Home inspectors", "Appraisers", "Title & escrow signing",
      "Photographers", "Short-term rental hosts"
    ]
  },
  {
    category: "Events & Entertainment",
    icon: EventsEntertainment,
    subcategories: [
      "Event planners", "Caterers", "Bakers", "Bartenders", "DJs & live bands",
      "Event rentals", "Photo booths", "Venues", "Florists"
    ]
  },
  {
    category: "Beauty & Wellness",
    icon: BeautyWellness,
    subcategories: [
      "Hair salons", "Makeup artists", "Nail salons", "Massage therapists",
      "Estheticians", "Personal trainers", "Studios", "Nutrition coaching",
      "Tanning & whitening"
    ]
  },
  {
    category: "Kids & Education",
    icon: KidsEducation,
    subcategories: [
      "Tutoring", "Music/art classes", "Day camps", "Nannies",
      "Party entertainers", "College counseling", "Homeschool support"
    ]
  },
  {
    category: "Pets",
    icon: Pets,
    subcategories: ["Grooming", "Dog walkers & sitters", "Training", "Photography", "Specialty products"]
  },
  {
    category: "Food & Beverage",
    icon: FoodBeverage,
    subcategories: ["Meal prep", "Specialty grocers", "Coffee carts", "Food trucks", "Dining clubs", "Beverage services"]
  },
  {
    category: "Apparel & Goods",
    icon: ApparelGoods,
    subcategories: ["Tailors", "Custom apparel", "Personal stylists", "Jewelry", "Consignment"]
  },
  {
    category: "Creative & Digital",
    icon: CreativeDigital,
    subcategories: [
      "Brand strategy", "Graphic design", "Web design", "SEO", "Paid ads",
      "Social media", "Email marketing", "Copywriting", "Video production",
      "Podcast production", "PR", "Photography", "Animation"
    ]
  },
  {
    category: "Technology & IT",
    icon: TechnologyIT,
    subcategories: [
      "Managed IT", "Cybersecurity", "Network cabling", "Cloud services", "Custom software",
      "No-code/low-code", "Data analytics", "POS setup", "AI implementation", "AR/VR"
    ]
  },
  {
    category: "Business Services",
    icon: BusinessServices,
    subcategories: [
      "Virtual assistants", "Bookkeeping", "HR consulting", "Payroll",
      "Operations", "Project management", "Translation", "Corporate training",
      "Print shops", "Office services", "Cleaning services"
    ]
  },
  {
    category: "Manufacturing",
    icon: Manufacturing,
    subcategories: ["Light manufacturing", "CNC machining", "Cabinetry", "Packaging design", "Safety training", "Equipment service"]
  },
  {
    category: "Logistics",
    icon: Logistics,
    subcategories: ["Couriers", "Freight brokers", "Warehousing", "Records storage", "Notaries", "Device repair"]
  },
  {
    category: "Travel & Lifestyle",
    icon: TravelLifestyle,
    subcategories: ["Travel planners", "Tour operators", "House sitting", "Plantscaping", "Concierge", "Luxury rentals"]
  },
  {
    category: "Arts & Community",
    icon: ArtCommunity,
    subcategories: ["Galleries", "Music production", "Ticketing", "Nonprofits", "Community organizers"]
  },
  {
    category: "Agriculture",
    icon: Agriculture,
    subcategories: ["Urban farming", "Beekeeping", "Firewood/compost", "Outdoor guides"]
  },
  {
    category: "Security",
    icon: Security,
    subcategories: ["Private security", "Background checks", "Workplace safety"]
  },
  {
    category: "Specialty",
    icon: IndustryLogo, // ❌ placeholder
    subcategories: [
      "Photo digitization", "Heirloom services", "Luxury authentication",
      "Sustainability", "Accessibility audits", "Mobile labs"
    ]
  }
];
