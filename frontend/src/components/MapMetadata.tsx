import { useEffect, useRef, useState } from "react";
import { Box, Center, Spinner } from "@chakra-ui/react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:5000";

interface InstitutionRecord {
  id: string;
  display_name: string;
  lat: number;
  lng: number;
  authors: { id: string; name: string }[];
}

type Color = "blue" | "green" | "violet" | "orange" | "red";

const buildIcon = (color: Color) =>
  L.icon({
    iconUrl: `/assets/map_markers/marker-icon-${color}.png`,
    shadowUrl: "https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  });

const addLegend = (
  map: L.Map,
  ranges: { min: number; max: number; color: Color }[],
) => {
  const legend = new L.Control({ position: "bottomright" });
  legend.onAdd = () => {
    const div = L.DomUtil.create("div");
    div.innerHTML = `
      <div style="background: rgba(255,255,255,0.8); padding: 10px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.15); font-size: 14px;">
        <strong>Authors per Institution</strong><br/>
        <table style="border-collapse: collapse; margin-top: 4px;">
          ${ranges
            .map(
              ({ min, max, color }) => `
            <tr>
              <td><img src="/assets/map_markers/marker-icon-${color}.png" style="width: 20px; height: 34px;" /></td>
              <td style="padding-left:4px;">${min}&nbsp;–&nbsp;${max}</td>
            </tr>`,
            )
            .join("")}
        </table>
      </div>`;
    return div;
  };
  legend.addTo(map);
  return legend;
};

const MapMetadata = () => {
  const mapRef = useRef<L.Map | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const buildMap = async () => {
      try {
        const idsRes = await fetch(`${BACKEND_URL}/faculty_openalex_ids`);
        const AUTHOR_IDS: string[] = await idsRes.json();
        if (!AUTHOR_IDS.length) throw new Error("No author IDs found from backend");
        const authorUrl =
          `https://api.openalex.org/authors?filter=id:${AUTHOR_IDS.join("|")}` +
          `&select=id,display_name,last_known_institutions&per-page=50`;
        const authorRes = await fetch(authorUrl);
        const authorJson = await authorRes.json();
        const buckets: Record<string, InstitutionRecord> = {};
        (authorJson.results || []).forEach((a: any) => {
          const inst = a.last_known_institutions?.[0];
          if (!inst?.id) return;
          const key = inst.id.replace("https://openalex.org/", "");
          if (!buckets[key]) {
            buckets[key] = {
              id: key,
              display_name: inst.display_name ?? key,
              lat: 0,
              lng: 0,
              authors: [],
            };
          }
          buckets[key].authors.push({ id: a.id, name: a.display_name });
        });
        const institutionIds = Object.keys(buckets);
        if (!institutionIds.length) throw new Error("No institution IDs found.");
        const instUrl =
          `https://api.openalex.org/institutions?filter=id:${institutionIds.join("|")}` +
          `&select=id,display_name,geo&per-page=50`;
        const instRes = await fetch(instUrl);
        const instJson = await instRes.json();
        (instJson.results || []).forEach((inst: any) => {
          const key = inst.id.replace("https://openalex.org/", "");
          const bucket = buckets[key];
          if (!bucket) return;
          const { latitude, longitude } = inst.geo || {};
          if (latitude == null || longitude == null) return;
          bucket.lat = latitude;
          bucket.lng = longitude;
          bucket.display_name = inst.display_name;
        });
        const points = Object.values(buckets).filter((b) => b.lat && b.lng);
        if (!points.length) throw new Error("No mappable points.");
        const maxAuthors = Math.max(...points.map((p) => p.authors.length));
        const step = Math.max(1, Math.ceil(maxAuthors / 5));
        const thresholds = [0, step, step * 2, step * 3, step * 4];
        const colors: Color[] = ["blue", "green", "violet", "orange", "red"];
        const colourFor = (count: number): Color => {
          if (count >= thresholds[4]) return "red";
          if (count >= thresholds[3]) return "orange";
          if (count >= thresholds[2]) return "violet";
          if (count >= thresholds[1]) return "green";
          return "blue";
        };
        if (mapRef.current) {
          mapRef.current.remove();
          mapRef.current = null;
        }
        const container = L.DomUtil.get("map-container");
        if (container && (container as any)._leaflet_id) (container as any)._leaflet_id = undefined;
        const map = L.map("map-container", { scrollWheelZoom: false }).setView(
          [points[0].lat, points[0].lng],
          5,
        );
        mapRef.current = map;
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
        }).addTo(map);
        points.forEach((p) => {
          const htmlAuthors = p.authors.map((a) => a.name).join("<br/>");
          const color = colourFor(p.authors.length);
          L.marker([p.lat, p.lng], { icon: buildIcon(color) })
            .addTo(map)
            .bindPopup(`<strong>${p.display_name}</strong><br/>${htmlAuthors}`);
        });
        const ranges = colors.map((c, idx) => {
          const min = thresholds[idx];
          const max = idx === 4 ? maxAuthors : thresholds[idx + 1] - 1;
          return { min, max, color: c } as const;
        });
        addLegend(map, ranges);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    };
    buildMap();
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  return (
    <Box width="100%" height="500px" position="relative">
      {loading && (
        <Center position="absolute" top={0} left={0} w="100%" h="100%" zIndex={10} bg="rgba(255,255,255,0.6)">
          <Spinner size="xl" thickness="4px" speed="0.65s" color="blue.500" />
        </Center>
      )}
      <div id="map-container" style={{ width: "100%", height: "100%" }} />
    </Box>
  );
};

export default MapMetadata;
