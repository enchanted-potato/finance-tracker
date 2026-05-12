import { NavLink } from 'react-router-dom';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar';

// D-05: Sidebar page order matches existing Streamlit app
const navItems = [
  { to: '/',            label: 'Dashboard' },
  { to: '/accounts',   label: 'Accounts' },
  { to: '/liabilities', label: 'Liabilities' },
  { to: '/pension',    label: 'Pension' },
  { to: '/history',    label: 'History' },
  { to: '/configure',  label: 'Configure' },
];

export function AppSidebar() {
  return (
    <Sidebar collapsible="none" className="w-[240px] bg-card border-r border-border">
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map(({ to, label }) => (
                <SidebarMenuItem key={to}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={to}
                      end={to === '/'}
                      className={({ isActive }) =>
                        isActive
                          ? 'text-[#58a6ff] font-semibold border-l-2 border-[#58a6ff] py-2 px-4 block transition-colors duration-150'
                          : 'py-2 px-4 block transition-colors duration-150 hover:bg-white/5'
                      }
                    >
                      {label}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
