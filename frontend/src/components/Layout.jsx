import { useState } from "react";
import MenuIcon from "@mui/icons-material/Menu";
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useNavigate } from "react-router-dom";

const drawerWidth = 220;

export default function Layout({ children }) {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const handleNav = (path) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const drawerContent = (
    <>
      <Box sx={{ p: 3 }}>
        <Typography sx={{ fontWeight: 700, fontSize: 19, letterSpacing: 0.2 }}>
          Pneumonia Vision
        </Typography>
        <Typography sx={{ fontSize: 12, color: "#a7bfd9", mt: 0.5 }}>
          Clinical AI Workspace
        </Typography>
      </Box>

      <List>
        <ListItemButton sx={{ mx: 1, borderRadius: 2 }} onClick={() => handleNav("/")}>
          <ListItemText primary="Upload" />
        </ListItemButton>

        <ListItemButton sx={{ mx: 1, borderRadius: 2 }} onClick={() => handleNav("/dashboard")}>
          <ListItemText primary="Dashboard" />
        </ListItemButton>

        <ListItemButton sx={{ mx: 1, borderRadius: 2 }} onClick={() => handleNav("/history")}>
          <ListItemText primary="History" />
        </ListItemButton>

        <ListItemButton sx={{ mx: 1, borderRadius: 2 }} onClick={handleLogout}>
          <ListItemText primary="Logout" />
        </ListItemButton>
      </List>
    </>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", color: "#eff7ff" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          display: { xs: "block", md: "none" },
          background: "rgba(6, 20, 34, 0.88)",
          borderBottom: "1px solid rgba(163, 204, 255, 0.25)",
          backdropFilter: "blur(8px)",
        }}
      >
        <Toolbar sx={{ minHeight: 62 }}>
          <IconButton edge="start" color="inherit" onClick={() => setMobileOpen(true)}>
            <MenuIcon />
          </IconButton>
          <Typography sx={{ fontWeight: 700, ml: 1 }}>Pneumonia Vision</Typography>
        </Toolbar>
      </AppBar>

      <Drawer
        variant={isMobile ? "temporary" : "permanent"}
        open={isMobile ? mobileOpen : true}
        onClose={() => setMobileOpen(false)}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            background:
              "linear-gradient(190deg, rgba(11, 31, 49, 0.95), rgba(6, 20, 34, 0.95))",
            color: "#eff7ff",
            borderRight: "1px solid rgba(163, 204, 255, 0.25)",
            boxShadow: "8px 0 40px rgba(0, 0, 0, 0.35)",
          },
        }}
      >
        {drawerContent}
      </Drawer>

      <Box
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 4 },
          mt: { xs: 8, md: 0 },
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
