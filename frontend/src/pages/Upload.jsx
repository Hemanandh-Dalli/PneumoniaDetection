import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Typography, Button, Box, Paper } from "@mui/material";
import API from "../api/api";
import { motion } from "framer-motion";
import Layout from "../components/Layout";

function Upload() {
  const [file, setFile] = useState(null);
  const navigate = useNavigate();

  const handleUpload = async () => {
    if (!file) {
      alert("Please select an X-ray image");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await API.post("/predict", formData);
      navigate("/result", { state: res.data });
    } catch (err) {
      alert("Prediction failed");
    }
  };

  return (
    <Layout>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <Container maxWidth="sm" sx={{ mt: { xs: 2, md: 5 } }}>
          <Paper className="glass-3d float-card" sx={{ p: { xs: 3, md: 4 } }}>
            <Typography className="page-title" gutterBottom>
              Upload X-ray
            </Typography>

            <Typography className="page-subtitle" sx={{ mb: 3 }}>
              Add a chest X-ray image to generate prediction, heatmap, and explanation.
            </Typography>

            <Box
              sx={{
                mt: 2,
                p: 2,
                border: "1px dashed rgba(163, 204, 255, 0.5)",
                borderRadius: 2,
                background: "rgba(255, 255, 255, 0.03)",
              }}
            >
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files[0])}
                style={{ color: "#eff7ff", width: "100%" }}
              />
            </Box>

            <Button
              className="cta-btn"
              variant="contained"
              fullWidth
              sx={{
                mt: 3,
                background: "linear-gradient(135deg, #3ad6ff, #41b2ff)",
              }}
              onClick={handleUpload}
            >
              Upload and Classify
            </Button>
          </Paper>
        </Container>
      </motion.div>
    </Layout>
  );
}

export default Upload;
