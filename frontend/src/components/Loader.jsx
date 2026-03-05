import { CircularProgress, Box } from "@mui/material";

export default function Loader() {
  return (
    <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
      <CircularProgress color="info" />
    </Box>
  );
}

