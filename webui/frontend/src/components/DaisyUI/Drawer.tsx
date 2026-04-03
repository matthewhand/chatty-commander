import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ChevronRight, ChevronDown } from 'lucide-react';

export interface DrawerNavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path?: string;
  badge?: string | number;
  children?: DrawerNavItem[];
  disabled?: boolean;
  divider?: boolean;
}

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  navItems?: DrawerNavItem[];
  variant?: 'sidebar' | 'mobile' | 'overlay';
  className?: string;
  children?: React.ReactNode;
}

const Drawer: React.FC<DrawerProps> = ({ isOpen, onClose, navItems = [], variant = 'sidebar', className = '', children }) => {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const findParents = (items: DrawerNavItem[], path: string, parents: string[] = []): string[] => {
      for (const item of items) {
        if (item.path === path) return parents;
        if (item.children) { const r = findParents(item.children, path, [...parents, item.id]); if (r.length > 0) return r; }
      }
      return [];
    };
    const parents = findParents(navItems, location.pathname);
    if (parents.length > 0) setExpandedItems(new Set(parents));
  }, [location.pathname, navItems]);

  useEffect(() => {
    if (variant === 'sidebar' || !isOpen) return;
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen, onClose, variant]);

  const toggleExpanded = useCallback((id: string) => {
    setExpandedItems(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s; });
  }, []);

  const handleNav = useCallback((path: string) => {
    navigate(path);
    if (variant !== 'sidebar') onClose();
  }, [navigate, onClose, variant]);

  const renderItem = (item: DrawerNavItem, depth = 0) => {
    const isActive = item.path && (location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path + '/')));
    const isExpanded = expandedItems.has(item.id);
    const hasChildren = item.children && item.children.length > 0;

    if (item.divider) {
      return (
        <div key={item.id} className="pt-4 pb-2 px-4 mt-2">
          {item.label && <span className="text-[11px] font-semibold uppercase tracking-wider text-base-content/50">{item.label}</span>}
        </div>
      );
    }

    return (
      <li key={item.id} style={{ marginLeft: depth > 0 ? '12px' : 0 }}>
        <button type="button" disabled={item.disabled} aria-expanded={hasChildren ? isExpanded : undefined} aria-current={isActive ? 'page' : undefined} role="menuitem"
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); if (item.disabled) return; item.path ? handleNav(item.path) : hasChildren && toggleExpanded(item.id); }}
          className={`flex items-center w-full px-3 py-2.5 rounded-lg border-none text-[14px] font-medium text-left transition-colors duration-150 ease-in-out ${isActive ? 'bg-primary text-primary-content' : 'bg-transparent text-base-content hover:bg-base-content/10'} ${item.disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
          <span className={`mr-3 ${isActive ? 'text-primary-content' : 'text-base-content/60'}`} aria-hidden="true">{item.icon}</span>
          <span className="flex-1">{item.label}</span>
          {item.badge && <span className={`text-[11px] px-1.5 py-0.5 rounded-full ml-2 ${isActive ? 'bg-primary-content/20 text-primary-content' : 'bg-primary text-primary-content'}`}>{item.badge}</span>}
          {hasChildren && <span className={`ml-2 ${isActive ? 'text-primary-content' : 'text-base-content/60'}`}>{isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</span>}
        </button>
        {hasChildren && isExpanded && <ul className="list-none m-0 mt-1 p-0">{item.children!.map(c => renderItem(c, depth + 1))}</ul>}
      </li>
    );
  };

  return (
    <aside className={`h-full flex flex-col bg-base-300 text-base-content ${className}`} role="navigation" aria-label="Sidebar navigation">
      <nav className="flex-1 overflow-y-auto flex flex-col" aria-label="Main menu">
        {navItems.length > 0 && <ul className="list-none m-0 p-2">{navItems.map(item => renderItem(item))}</ul>}
        {children}
      </nav>
    </aside>
  );
};

export default Drawer;
