import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Github, TrendingUp, Award, Activity, Calendar, Users, GitBranch, Star } from 'lucide-react';
import ScoreGauge from '../../components/footprint/ScoreGauge';
import GitHubContributionGraph from '../../components/footprint/GitHubContributionGraph';
import ActivityChart from '../../components/footprint/ActivityChart';
import RecommendationsList from '../../components/footprint/RecommendationsList';
import FootprintScanForm from '../../components/footprint/FootprintScanForm';
import { API_BASE_URL } from '../../services/api-config';

interface FootprintScan {
  id: number;
  overall_score: number;
  github_score: number | null;
  stackoverflow_score: number | null;
  visibility_score: number;
  activity_score: number;
  impact_score: number;
  expertise_score: number;
  performance_level: string;
  scanned_at: string;
  github_data?: {
    profile: {
      name: string;
      bio: string;
      avatar_url: string;
      public_repos: number;
      followers: number;
      following: number;
    };
    repositories: {
      total_stars: number;
      total_forks: number;
      top_repos: Array<{
        name: string;
        stars: number;
        language: string;
      }>;
      language_percentages?: Record<string, number>;
      skills?: {
        frameworks: Record<string, number>;
        databases: Record<string, number>;
        tools: Record<string, number>;
      };
    };
    activity: {
      commits: number;
      pull_requests: number;
      issues: number;
      activity_streak: number;
    };
  };
  stackoverflow_data?: {
    profile: {
      display_name: string;
      reputation: number;
      badge_counts: {
        gold: number;
        silver: number;
        bronze: number;
      };
    };
  };
}

export default function FootprintPage() {
  const [latestScan, setLatestScan] = useState<FootprintScan | null>(null);
  const [scanHistory, setScanHistory] = useState<FootprintScan[]>([]);
  const [loading, setLoading] = useState(true);
  const [showScanForm, setShowScanForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFootprintData();
  }, []);

  const fetchFootprintData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // First, try to get scan history
      const historyResponse = await fetch(`${API_BASE_URL}/footprint/history?limit=10`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        console.log('History data received:', historyData);
        
        if (historyData.scans && historyData.scans.length > 0) {
          const latestHistoryItem = historyData.scans[0];
          
          // Fetch full scan details for the latest scan
          const detailsResponse = await fetch(`${API_BASE_URL}/footprint/${latestHistoryItem.scan_id}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (detailsResponse.ok) {
            const detailsData = await detailsResponse.json();
            console.log('Scan details received:', detailsData);
            
            // Transform the backend response to match frontend interface
            const transformedScan: FootprintScan = {
              id: detailsData.scan_id,
              overall_score: detailsData.overall_visibility_score || 0,
              github_score: detailsData.github_analysis?.scores?.overall_github_score || null,
              stackoverflow_score: detailsData.stackoverflow_analysis?.scores?.overall_stackoverflow_score || null,
              visibility_score: detailsData.visibility_score || 0,
              activity_score: detailsData.activity_score || 0,
              impact_score: detailsData.impact_score || 0,
              expertise_score: detailsData.expertise_score || 0,
              performance_level: getPerformanceLevel(detailsData.overall_visibility_score || 0),
              scanned_at: detailsData.scanned_at,
              github_data: detailsData.github_analysis ? {
                profile: {
                  name: detailsData.github_analysis.profile.name || detailsData.github_analysis.profile.username,
                  bio: detailsData.github_analysis.profile.bio || '',
                  avatar_url: '',
                  public_repos: detailsData.github_analysis.profile.public_repos,
                  followers: detailsData.github_analysis.profile.followers,
                  following: detailsData.github_analysis.profile.following
                },
                repositories: {
                  total_stars: detailsData.github_analysis.total_stars,
                  total_forks: detailsData.github_analysis.total_forks,
                  top_repos: detailsData.github_analysis.top_repositories.map((r: any) => ({
                    name: r.name,
                    stars: r.stars,
                    language: r.language
                  })),
                  language_percentages: detailsData.github_analysis.languages || {},
                  skills: detailsData.github_analysis.skills ? {
                    frameworks: detailsData.github_analysis.skills.frameworks || {},
                    databases: detailsData.github_analysis.skills.databases || {},
                    tools: detailsData.github_analysis.skills.tools || {}
                  } : undefined
                },
                activity: {
                  commits: detailsData.github_analysis.activity.commits,
                  pull_requests: detailsData.github_analysis.activity.pull_requests,
                  issues: detailsData.github_analysis.activity.issues,
                  activity_streak: detailsData.github_analysis.activity.activity_streak
                }
              } : undefined,
              stackoverflow_data: detailsData.stackoverflow_analysis ? {
                profile: {
                  display_name: detailsData.stackoverflow_analysis.profile.display_name,
                  reputation: detailsData.stackoverflow_analysis.profile.reputation,
                  badge_counts: {
                    gold: detailsData.stackoverflow_analysis.profile.badges.gold,
                    silver: detailsData.stackoverflow_analysis.profile.badges.silver,
                    bronze: detailsData.stackoverflow_analysis.profile.badges.bronze
                  }
                }
              } : undefined
            };
            
            setLatestScan(transformedScan);
            
            // Transform history items
            const transformedHistory = historyData.scans.map((item: any) => ({
              id: item.scan_id,
              scanned_at: item.scanned_at,
              overall_score: item.overall_visibility_score || 0,
              github_score: item.github_score,
              stackoverflow_score: item.stackoverflow_score,
              visibility_score: item.visibility_score || 0,
              activity_score: item.activity_score || 0,
              impact_score: item.impact_score || 0,
              expertise_score: item.expertise_score || 0,
              performance_level: getPerformanceLevel(item.overall_visibility_score || 0)
            }));
            
            setScanHistory(transformedHistory);
            setError(null);
          } else {
            console.error('Failed to fetch scan details:', detailsResponse.status);
            setError('Failed to load scan details');
          }
        } else {
          console.log('No scans found in history');
          setLatestScan(null);
          setScanHistory([]);
        }
      } else {
        console.error('Failed to fetch history:', historyResponse.status, historyResponse.statusText);
        setError(`Failed to load data: ${historyResponse.statusText}`);
      }
    } catch (error) {
      console.error('Failed to fetch footprint data:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceLevel = (score: number): string => {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'average';
    return 'needs_improvement';
  };

  const handleScanComplete = () => {
    setShowScanForm(false);
    fetchFootprintData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-2xl mx-auto text-center bg-red-50 border border-red-200 rounded-xl p-8">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => {
              setError(null);
              setLoading(true);
              fetchFootprintData();
            }}
            className="px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!latestScan && !showScanForm) {
    return (
      <div className="p-8 bg-gray-50 min-h-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl mx-auto text-center"
        >
          <div className="bg-white rounded-3xl p-12 border border-gray-200 shadow-lg">
            <div className="w-24 h-24 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <TrendingUp className="w-12 h-12 text-primary-600" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Track Your Professional Footprint
            </h1>
            <p className="text-gray-600 text-lg mb-8">
              Analyze your GitHub contributions and Stack Overflow activity to get a comprehensive professional score.
            </p>
            <button
              onClick={() => setShowScanForm(true)}
              className="px-8 py-4 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors shadow-md"
            >
              Start Your First Scan
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  if (showScanForm) {
    return (
      <FootprintScanForm
        onComplete={handleScanComplete}
        onCancel={() => setShowScanForm(false)}
      />
    );
  }

  // Safety check - don't render if no data
  if (!latestScan) {
    return (
      <div className="p-8 bg-gray-50 min-h-full">
        <div className="text-center text-gray-500">
          <p>No footprint data available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-8 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-between items-center"
        >
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Professional Footprint
            </h1>
            <p className="text-gray-600">
              Last scanned: {new Date(latestScan.scanned_at).toLocaleDateString()}
            </p>
          </div>
          <button
            onClick={() => setShowScanForm(true)}
            className="px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors shadow-md"
          >
            New Scan
          </button>
        </motion.div>

        {/* Main Score */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-3xl p-8 border border-gray-200 shadow-lg"
        >
          <div className="grid md:grid-cols-2 gap-8">
            <div className="flex flex-col items-center justify-center">
              <ScoreGauge score={latestScan.overall_score} size={240} />
              <div className="mt-6 text-center">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Overall Score
                </h2>
                <span className={`inline-block px-4 py-2 rounded-full text-sm font-semibold ${
                  latestScan.performance_level === 'excellent' ? 'bg-green-500/20 text-green-400' :
                  latestScan.performance_level === 'good' ? 'bg-blue-500/20 text-blue-400' :
                  latestScan.performance_level === 'average' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-red-500/20 text-red-400'
                }`}>
                  {latestScan.performance_level.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Dimension Scores */}
              <DimensionCard
                icon={<Users className="w-6 h-6" />}
                title="Visibility"
                score={latestScan.visibility_score}
                color="sky"
              />
              <DimensionCard
                icon={<Activity className="w-6 h-6" />}
                title="Activity"
                score={latestScan.activity_score}
                color="purple"
              />
              <DimensionCard
                icon={<TrendingUp className="w-6 h-6" />}
                title="Impact"
                score={latestScan.impact_score}
                color="green"
              />
              <DimensionCard
                icon={<Award className="w-6 h-6" />}
                title="Expertise"
                score={latestScan.expertise_score}
                color="orange"
              />
            </div>
          </div>
        </motion.div>

        {/* GitHub Section - Full Width */}
        {latestScan.github_data && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl p-8 border border-gray-200 shadow-md"
          >
            {/* GitHub Profile Header */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
                <Github className="w-7 h-7 text-gray-900" />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-gray-900">GitHub Analysis</h3>
                <p className="text-gray-600 text-sm">Score: {latestScan.github_score}/100</p>
              </div>
            </div>

            {/* Profile Name & Bio */}
            {latestScan.github_data.profile.name && (
              <div className="mb-6 pb-6 border-b border-gray-200">
                <p className="text-lg font-semibold text-gray-900">
                  {latestScan.github_data.profile.name}
                </p>
                {latestScan.github_data.profile.bio && (
                  <p className="text-sm text-gray-600 mt-1">
                    {latestScan.github_data.profile.bio}
                  </p>
                )}
              </div>
            )}

            {/* Stats Grid - 4 columns on desktop */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-700 mb-1">
                  <GitBranch className="w-5 h-5 text-primary-600" />
                  <span className="text-sm">Repositories</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {latestScan.github_data.profile.public_repos}
                </p>
              </div>
              
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-700 mb-1">
                  <Star className="w-5 h-5 text-yellow-500" />
                  <span className="text-sm">Total Stars</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {latestScan.github_data.repositories.total_stars}
                </p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-700 mb-1">
                  <Users className="w-5 h-5 text-purple-500" />
                  <span className="text-sm">Followers</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {latestScan.github_data.profile.followers}
                </p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-700 mb-1">
                  <Activity className="w-5 h-5 text-green-500" />
                  <span className="text-sm">Commits</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {latestScan.github_data.activity.commits}
                </p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-700 mb-1">
                  <GitBranch className="w-5 h-5 text-blue-500" />
                  <span className="text-sm">Total Forks</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {latestScan.github_data.repositories.total_forks}
                </p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-700 mb-1">
                  <Users className="w-5 h-5 text-pink-500" />
                  <span className="text-sm">Following</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {latestScan.github_data.profile.following}
                </p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-700 mb-1">
                  <TrendingUp className="w-5 h-5 text-orange-500" />
                  <span className="text-sm">Pull Requests</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {latestScan.github_data.activity.pull_requests}
                </p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-700 mb-1">
                  <Activity className="w-5 h-5 text-green-500" />
                  <span className="text-sm">Activity Streak</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {latestScan.github_data.activity.activity_streak} days
                </p>
              </div>
            </div>

              {/* Programming Languages Breakdown - CENTERED IN CARD */}
              {latestScan.github_data.repositories.language_percentages && 
               Object.keys(latestScan.github_data.repositories.language_percentages).length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-primary-600" />
                    Programming Languages
                  </h4>
                  <div className="space-y-2.5">
                    {Object.entries(latestScan.github_data.repositories.language_percentages)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 5)
                      .map(([lang, percentage]) => {
                        const getLanguageColor = (language: string) => {
                          const colors: Record<string, string> = {
                            'TypeScript': 'bg-blue-500',
                            'JavaScript': 'bg-yellow-500',
                            'Python': 'bg-green-500',
                            'Java': 'bg-red-500',
                            'C++': 'bg-pink-500',
                            'C#': 'bg-purple-500',
                            'Go': 'bg-cyan-500',
                            'Rust': 'bg-orange-500',
                            'PHP': 'bg-indigo-500',
                            'Ruby': 'bg-red-600',
                            'Swift': 'bg-orange-600',
                            'Kotlin': 'bg-purple-600',
                            'HTML': 'bg-orange-400',
                            'CSS': 'bg-blue-400',
                            'Vue': 'bg-green-400'
                          };
                          return colors[language] || 'bg-gray-500';
                        };

                        const barBlocks = Math.round(percentage / 4);
                        
                        return (
                          <div key={lang} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-medium text-gray-700">{lang}</span>
                              <span className="text-gray-600 font-semibold">{percentage.toFixed(2)}%</span>
                            </div>
                            <div className="flex gap-0.5">
                              {Array.from({ length: 25 }).map((_, i) => (
                                <div
                                  key={i}
                                  className={`h-2 flex-1 rounded-sm ${
                                    i < barBlocks ? getLanguageColor(lang) : 'bg-gray-200'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}

              {/* Skills & Technologies Section */}
              {latestScan.github_data.repositories.skills && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h4 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Award className="w-4 h-4 text-primary-600" />
                    Skills & Technologies
                  </h4>
                  
                  {/* Frameworks */}
                  {Object.keys(latestScan.github_data.repositories.skills.frameworks).length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs font-semibold text-gray-600 mb-2">Frameworks & Libraries</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(latestScan.github_data.repositories.skills.frameworks)
                          .sort((a, b) => b[1] - a[1])
                          .slice(0, 6)
                          .map(([skill, count]) => (
                            <span
                              key={skill}
                              className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium border border-blue-200"
                              title={`Used in ${count} ${count === 1 ? 'project' : 'projects'}`}
                            >
                              {skill}
                              <span className="ml-1 text-blue-600 font-bold">{count}</span>
                            </span>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Databases */}
                  {Object.keys(latestScan.github_data.repositories.skills.databases).length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs font-semibold text-gray-600 mb-2">Databases</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(latestScan.github_data.repositories.skills.databases)
                          .sort((a, b) => b[1] - a[1])
                          .map(([skill, count]) => (
                            <span
                              key={skill}
                              className="px-2.5 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium border border-green-200"
                              title={`Used in ${count} ${count === 1 ? 'project' : 'projects'}`}
                            >
                              {skill}
                              <span className="ml-1 text-green-600 font-bold">{count}</span>
                            </span>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Tools & Platforms */}
                  {Object.keys(latestScan.github_data.repositories.skills.tools).length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-600 mb-2">Tools & Platforms</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(latestScan.github_data.repositories.skills.tools)
                          .sort((a, b) => b[1] - a[1])
                          .slice(0, 8)
                          .map(([skill, count]) => (
                            <span
                              key={skill}
                              className="px-2.5 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium border border-purple-200"
                              title={`Used in ${count} ${count === 1 ? 'project' : 'projects'}`}
                            >
                              {skill}
                              <span className="ml-1 text-purple-600 font-bold">{count}</span>
                            </span>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
          </motion.div>
        )}

        {/* StackOverflow Section - Full Width */}
        {latestScan.stackoverflow_data && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl p-8 border border-gray-200 shadow-md"
          >
              {/* StackOverflow Profile Header */}
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 bg-orange-50 rounded-xl flex items-center justify-center">
                  <span className="text-orange-600 font-bold text-xl">SO</span>
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900">Stack Overflow</h3>
                  <p className="text-gray-600 text-sm">Score: {latestScan.stackoverflow_score}/100</p>
                </div>
              </div>

              {/* Profile Name */}
              <div className="mb-4 pb-4 border-b border-gray-200">
                <p className="text-lg font-semibold text-gray-900">
                  {latestScan.stackoverflow_data.profile.display_name}
                </p>
              </div>

              {/* Stats */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-gray-700">
                    <TrendingUp className="w-5 h-5 text-orange-500" />
                    <span>Reputation</span>
                  </div>
                  <span className="text-gray-900 font-semibold">
                    {latestScan.stackoverflow_data.profile.reputation.toLocaleString()}
                  </span>
                </div>
                
                {/* Badges */}
                <div className="pt-2 pb-2 border-t border-gray-100">
                  <p className="text-xs font-semibold text-gray-500 mb-2 uppercase">Badges</p>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="flex flex-col items-center p-2 bg-yellow-50 rounded-lg">
                      <div className="w-4 h-4 rounded-full bg-yellow-500 mb-1"></div>
                      <span className="text-xs text-gray-600">Gold</span>
                      <span className="text-lg font-bold text-gray-900">
                        {latestScan.stackoverflow_data.profile.badge_counts.gold}
                      </span>
                    </div>
                    <div className="flex flex-col items-center p-2 bg-gray-50 rounded-lg">
                      <div className="w-4 h-4 rounded-full bg-gray-400 mb-1"></div>
                      <span className="text-xs text-gray-600">Silver</span>
                      <span className="text-lg font-bold text-gray-900">
                        {latestScan.stackoverflow_data.profile.badge_counts.silver}
                      </span>
                    </div>
                    <div className="flex flex-col items-center p-2 bg-orange-50 rounded-lg">
                      <div className="w-4 h-4 rounded-full bg-orange-700 mb-1"></div>
                      <span className="text-xs text-gray-600">Bronze</span>
                      <span className="text-lg font-bold text-gray-900">
                        {latestScan.stackoverflow_data.profile.badge_counts.bronze}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* GitHub Contribution Graph */}
          {latestScan.github_data && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white rounded-2xl p-6 border border-gray-200 shadow-md"
            >
              <div className="flex items-center gap-3 mb-6">
                <Calendar className="w-6 h-6 text-primary-600" />
                <h3 className="text-xl font-bold text-gray-900">Contribution Activity</h3>
              </div>
              <GitHubContributionGraph scanId={latestScan.id} />
            </motion.div>
          )}

          {/* Activity Timeline */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl p-6 border border-gray-200 shadow-md"
          >
            <div className="flex items-center gap-3 mb-6">
              <Calendar className="w-6 h-6 text-primary-600" />
              <h3 className="text-xl font-bold text-gray-900">Contribution Activity</h3>
            </div>
            <ActivityChart scanHistory={scanHistory} />
          </motion.div>

          {/* Recommendations */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <RecommendationsList scanId={latestScan.id} />
          </motion.div>
      </div>
    </div>
  );
}

function DimensionCard({ icon, title, score, color }: {
  icon: React.ReactNode;
  title: string;
  score: number;
  color: string;
}) {
  const colorClasses = {
    sky: 'from-sky-500 to-blue-600',
    purple: 'from-purple-500 to-pink-600',
    green: 'from-green-500 to-emerald-600',
    orange: 'from-orange-500 to-red-600'
  };

  return (
    <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
      <div className={`w-10 h-10 bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} rounded-lg flex items-center justify-center mb-3 text-white`}>
        {icon}
      </div>
      <p className="text-gray-600 text-sm mb-1">{title}</p>
      <p className="text-2xl font-bold text-gray-900">{score}</p>
    </div>
  );
}
